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

# _pgsql = azure_native.dbforpostgresql.Server(
#             "appdb",
#             resource_group_name=self._rg,
#             sku=sku,
#             version="16",
#             auth_config=azure_native.dbforpostgresql.AuthConfigArgs(
#                 password_auth=azure_native.dbforpostgresql.PasswordAuthEnum.DISABLED,
#                 active_directory_auth=azure_native.dbforpostgresql.ActiveDirectoryAuthEnum.ENABLED,
#                 tenant_id=self._tenant_id,
#             ),
#             storage=azure_native.dbforpostgresql.StorageArgs(storage_size_gb=32),
#             network=azure_native.dbforpostgresql.NetworkArgs(
#                 delegated_subnet_resource_id=subnet.id,
#                 private_dns_zone_arm_resource_id=dns.id,
#             ),
#             backup=azure.dbforpostgresql.BackupArgs(
#                 backup_retention_days=7,
#                 geo_redundant_backup=azure.dbforpostgresql.GeoRedundantBackupEnum.DISABLED,
#             ),
#         )

# Create a database
# db = azure_native.dbforpostgresql.Database(
#     "appdb",
#     database_name="appdb",
#     resource_group_name=self._rg,
#     server_name=_pgsql.name,
# )

# Criar um banco de dados PostgreSQL usando `Server`
# postgres_server = azure_native.dbforpostgresql.Server(
#     "postgresql-server",
#     resource_group_name=resource_group.name,
#     administrator_login="admin",
#     administrator_login_password=admin_password,
#     version="11",  # Defina a versão do PostgreSQL
#     geo_redundant_backup="Disabled",  # Backup georredundante desativado
#     sku=azure_native.dbforpostgresql.SkuArgs(
#         name="B_Gen5_1",  # Nome do SKU
#         tier="Basic",     # Tipo de SKU
#      # Capacidade
#     ),
#     location=resource_group.location
# )

# Criar o banco de dados PostgreSQL dentro do servidor
# postgres_db = azure_native.dbforpostgresql.Database(
#     "appdb",
#     resource_group_name=resource_group.name,
#     server_name=postgres_server.name,
#     charset="UTF8",
#     collation="English_United States.1252"
# )

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
# pulumi.export("postgresql_connection_string", Output.concat(
#     "postgres://", postgres_server.administrator_login, ":", admin_password, "@",
#     postgres_server.name, ".postgres.database.azure.com:5432/appdb"
# ))
pulumi.export("app_service_name", app_service.name)
pulumi.export("resource_group_name", resource_group.name)