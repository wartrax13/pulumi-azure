import os
import pulumi
import pulumi_azure_native as azure
from django_deployment import DjangoDeployment

stack = pulumi.get_stack()
config = pulumi.Config()


# Create resource group
rg = azure.resources.ResourceGroup(f"rg-{stack}")

# Create VNet
vnet = azure.network.VirtualNetwork(
    f"vnet-{stack}",
    resource_group_name=rg.name,
    address_space=azure.network.AddressSpaceArgs(
        address_prefixes=["10.0.0.0/16"],
    ),
)

# Deploy the website and all its components
django = DjangoDeployment(
    stack,
    tenant_id=os.getenv('AZURE_TENANT_ID'),
    resource_group_name=rg.name,
    vnet=vnet,
    pgsql_ip_prefix="10.0.10.0/24",
    appservice_ip_prefix="10.0.20.0/24",
    app_service_sku=azure.web.SkuDescriptionArgs(
        name="B2",
        tier="Basic",
    ),
    storage_account_name="mystorageaccount",
    cdn_host="cdn.example.com",
)

django.add_django_website(
    name="web",
    db_name="mywebsite",
    repository_url="git@gitlab.com:project/website.git",
    repository_branch="main",
    website_hosts=["example.com", "www.example.com"],
    django_settings_module="mywebsite.settings.production",
    comms_data_location="europe",
    comms_domains=["mydomain.com"],
)

django.add_database_administrator(
    object_id="a1b2c3....",
    user_name="user@example.com",
    tenant_id="a1b2c3....",
)
