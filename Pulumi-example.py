import pulumi
import pulumi_azure_native as azure_native
from pulumi import Output
import os

# Senha do administrador do PostgreSQL (use uma variável de ambiente)
admin_password = os.getenv('ADMIN_PASSWORD', 'Admin@123')

# Criar um grupo de recursos
resource_group = azure_native.resources.ResourceGroup("app-resource-group")

# Criar um Redis para o Celery (Mova o Redis para cima, antes de ser referenciado)
redis_cache = azure_native.cache.Redis(
    "redis",
    resource_group_name=resource_group.name,
    sku=azure_native.cache.SkuArgs(
        name="Basic",
        family="C",
        capacity=0
    )
)

# Criar um banco de dados PostgreSQL
postgres_server = azure_native.dbforpostgresql.Server(
    "postgresql-server",
    resource_group_name=resource_group.name,
    sku=azure_native.dbforpostgresql.SkuArgs(
        name="B_Gen5_1",
        tier="Basic",
        capacity=1,
        family="Gen5"
    ),
    storage_profile=azure_native.dbforpostgresql.StorageProfileArgs(
        storage_mb=5120,
    ),
    administrator_login="admin",
    administrator_login_password=admin_password
)

# Criar o banco de dados PostgreSQL dentro do servidor
postgres_db = azure_native.dbforpostgresql.Database(
    "appdb",
    resource_group_name=resource_group.name,
    server_name=postgres_server.name,
    database_name="appdb",
    charset="UTF8",
    collation="English_United States.1252"
)

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
        linux_fx_version="PYTHON|3.9",
        app_settings=[
            azure_native.web.NameValuePairArgs(name="POSTGRES_DB", value="appdb"),
            azure_native.web.NameValuePairArgs(name="POSTGRES_USER", value="admin"),
            azure_native.web.NameValuePairArgs(name="POSTGRES_PASSWORD", value=admin_password),
            azure_native.web.NameValuePairArgs(name="DJANGO_SETTINGS_MODULE", value="your_project.settings"),
            azure_native.web.NameValuePairArgs(name="REDIS_URL", value=Output.concat("redis://", redis_cache.host_name, ":6379")),
        ]
    )
)

# Exportar URLs e Credenciais
pulumi.export("app_url", Output.concat("https://", app_service.default_host_name))
pulumi.export("postgresql_connection_string", Output.concat(
    "postgres://", postgres_server.administrator_login, ":", admin_password, "@",
    postgres_server.name, ".postgres.database.azure.com:5432/appdb"
))
pulumi.export("app_service_name", app_service.name)
