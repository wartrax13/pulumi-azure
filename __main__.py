import pulumi
import pulumi_azure_native as azure_native
from pulumi import Output
import os

# Senha do administrador do PostgreSQL (use uma variável de ambiente)
admin_password = os.getenv('ADMIN_PASSWORD', 'Admin@123')

# Criar um grupo de recursos
resource_group = azure_native.resources.ResourceGroup("app-resource-group")

# Criar um Redis para o Celery
redis_cache = azure_native.cache.Redis(
    "redis",
    resource_group_name=resource_group.name,
    sku=azure_native.cache.SkuArgs(
        name="Basic",
        family="C",
        capacity=0  # Definindo o Redis como Basic
    )
)


# Create a PostgreSQL server in the resource group
postgres_server = azure_native.dbforpostgresql.Server(
    "appdb",
    resource_group_name=resource_group.name,
    sku=azure_native.dbforpostgresql.SkuArgs(
        name="Standard_B2ms",
        tier="Burstable",
    ),
    version="16",
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

# Create PostgreSQL database once the server has been provisioned
# postgres_db = azure_native.dbforpostgresql.Database(
#     "appdb",
#     resource_group_name=resource_group.name,
#     server_name=postgres_server.name,  # Nome do servidor
#     charset="UTF8",  # Charset do banco de dados
#     collation="English_United States.1252"  # Collation do banco de dados
# )

############################################3
###########################################

# Criar um App Service Plan
app_service_plan = azure_native.web.AppServicePlan(
    "appServicePlan",
    resource_group_name=resource_group.name,
    sku=azure_native.web.SkuDescriptionArgs(
        name="B1",
        tier="Basic",
    )
)

# Criar o App Service para hospedar a aplicação Django
app_service = azure_native.web.WebApp(
    "django-app",
    resource_group_name=resource_group.name,
    server_farm_id=app_service_plan.id,
    site_config=azure_native.web.SiteConfigArgs(
        app_settings=[
            azure_native.web.NameValuePairArgs(name="POSTGRES_DB", value="appdb"),
            azure_native.web.NameValuePairArgs(name="POSTGRES_USER", value="admin"),
            azure_native.web.NameValuePairArgs(name="POSTGRES_PASSWORD", value=admin_password),
            azure_native.web.NameValuePairArgs(name="DJANGO_SETTINGS_MODULE", value="core.settings"),
            azure_native.web.NameValuePairArgs(name="REDIS_URL", value=Output.concat("redis://", redis_cache.host_name, ":6379")),
        ]
    ),
    location=resource_group.location
)

# Exportar URLs e Credenciais
pulumi.export("app_url", Output.concat("https://", app_service.default_host_name))
pulumi.export("app_service_name", app_service.name)
pulumi.export("resource_group_name", resource_group.name)