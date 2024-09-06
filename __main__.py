import pulumi
import pulumi_azure_native as azure_native

# Exemplo de criação de um grupo de recursos no Azure
resource_group = azure_native.resources.ResourceGroup("app-resource-group")

# Exporta o nome do grupo de recursos como uma saída
pulumi.export("resource_group_name", resource_group.name)