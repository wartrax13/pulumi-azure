import pulumi
import pulumi_azure_native as azure_native
from pulumi import Output
import os

# Senha do administrador do PostgreSQL (use uma variável de ambiente)
admin_password = os.getenv('ADMIN_PASSWORD', 'Admin@123')

# Criar um grupo de recursos
resource_group = azure_native.resources.ResourceGroup("rg-pulumi", location="Brazil South")

# Criar um Virtual Network (para comunicação privada)
vnet = azure_native.network.VirtualNetwork(
    "django-vnet",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    address_space=azure_native.network.AddressSpaceArgs(
        address_prefixes=["10.0.0.0/16"]
    )
)

# Criar Subnet para PostgreSQL e Redis dentro da VNet
subnet = azure_native.network.Subnet(
    "subnet",
    resource_group_name=resource_group.name,
    virtual_network_name=vnet.name,
    address_prefix="10.0.1.0/24",
    private_endpoint_network_policies="Disabled"
)
# Criar um servidor PostgreSQL
postgres_server = azure_native.dbforpostgresql.Server(
    "appdb-testando-pulumi-1",
    resource_group_name=resource_group.name,
    sku=azure_native.dbforpostgresql.SkuArgs(
        name="Standard_B2ms",
        tier="Burstable",
    ),
    version="16",
    administrator_login="admin_user",
    administrator_login_password=admin_password,
    auth_config=azure_native.dbforpostgresql.AuthConfigArgs(
        password_auth=azure_native.dbforpostgresql.PasswordAuthEnum.DISABLED,
        active_directory_auth=azure_native.dbforpostgresql.ActiveDirectoryAuthEnum.ENABLED,
        tenant_id=os.getenv('AZURE_TENANT_ID'),
    ),
    storage=azure_native.dbforpostgresql.StorageArgs(storage_size_gb=32),
    backup=azure_native.dbforpostgresql.BackupArgs(
        backup_retention_days=7,
        geo_redundant_backup=azure_native.dbforpostgresql.GeoRedundantBackupEnum.DISABLED,
    ),
)

# Criar o banco de dados PostgreSQL após o servidor estar pronto
db = azure_native.dbforpostgresql.Database(
    "db-testando-pulumi-1",
    database_name="testando-pulumi-1",
    resource_group_name=resource_group.name,
    server_name=postgres_server.name,
)

# Criar um Redis para o Celery
redis_cache = azure_native.cache.Redis(
    "redis-testando-pulumi-1",
    resource_group_name=resource_group.name,
    sku=azure_native.cache.SkuArgs(
        name="Basic",
        family="C",
        capacity=0  # Definindo o Redis como Basic
    )
)

# Private DNS Zone para Redis
redis_dns_zone = azure_native.network.PrivateZone(
    "redis-dns",
    resource_group_name=resource_group.name,
    location="Global",
    private_zone_name="privatelink.redis.cache.windows.net"
)

# Private DNS Zone para PostgreSQL
postgres_dns_zone = azure_native.network.PrivateZone(
    "postgres-dns",
    resource_group_name=resource_group.name,
    location="Global",  # DNS zones geralmente são globais
    private_zone_name="privatelink.postgres.database.azure.com"
)

# Criar um App Service Plan
app_service_plan = azure_native.web.AppServicePlan(
    "appservice-testando-pulumi-1",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    kind="linux",
    reserved=True,
    sku=azure_native.web.SkuDescriptionArgs(
        name="B1",
        tier="Basic",
    )
)

# Criar o App Service para hospedar a aplicação Django
app_service = azure_native.web.WebApp(
    "django-app-testando-pulumi-1",
    resource_group_name=resource_group.name,
    server_farm_id=app_service_plan.id,
    site_config=azure_native.web.SiteConfigArgs(
        linux_fx_version="PYTHON|3.10",
        app_settings=[
            azure_native.web.NameValuePairArgs(name="POSTGRES_DB", value="djangodb"),
            azure_native.web.NameValuePairArgs(name="POSTGRES_USER", value="admin_user"),
            azure_native.web.NameValuePairArgs(name="POSTGRES_PASSWORD", value=admin_password),
            azure_native.web.NameValuePairArgs(name="POSTGRES_HOST", value=Output.concat(postgres_server.name, ".postgres.database.azure.com")),
            azure_native.web.NameValuePairArgs(name="DJANGO_SETTINGS_MODULE", value="core.settings"),
            azure_native.web.NameValuePairArgs(name="REDIS_URL", value=Output.concat("redis://", redis_cache.host_name, ":6379")),
        ],
        # app_command_line="python manage.py migrate && python manage.py collectstatic --noinput"  # Comando múltiplo
    ),
    vnet_route_all_enabled=True,
    virtual_network_subnet_id=subnet.id,
    location=resource_group.location
)

# # Exportar URLs e Credenciais
pulumi.export("app_url", Output.concat("https://", app_service.default_host_name))
pulumi.export("app_service_name", app_service.name)
pulumi.export("resource_group_name", resource_group.name)
