import pulumi
import pulumi_azure_native as azure_native


resource_group = azure_native.resources.ResourceGroup(
    "app-resource-group",
    location="Brazil South"  # Localização no Brasil
)
pulumi.export("resource_group_name", resource_group.name)