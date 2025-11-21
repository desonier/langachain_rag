targetScope = 'resourceGroup'

@description('Name of the Azure App Service')
param appName string = 'resume-rag-app'

@description('Location for all resources')
param location string = resourceGroup().location

@description('The SKU of App Service Plan')
@allowed([
  'F1'
  'B1'
  'B2'
  'S1'
  'S2'
  'P1V2'
  'P2V2'
])
param appServicePlanSku string = 'B1'

@description('Azure Container Registry name')
param acrName string = 'resumeragacr${uniqueString(resourceGroup().id)}'

@description('Azure OpenAI endpoint URL')
@secure()
param azureOpenAiEndpoint string

@description('Azure OpenAI API key')
@secure()
param azureOpenAiKey string

@description('Azure OpenAI deployment name')
param azureOpenAiDeployment string = 'gpt-4'

@description('Azure OpenAI API version')
param azureOpenAiApiVersion string = '2024-02-15-preview'

@description('Docker image name')
param dockerImageName string = 'resume-rag-app'

@description('Docker image tag')
param dockerImageTag string = 'latest'

// Variables
var appServicePlanName = '${appName}-plan'
var logAnalyticsWorkspaceName = '${appName}-logs'
var appInsightsName = '${appName}-insights'

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Application Insights
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

// Azure Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  kind: 'linux'
  properties: {
    reserved: true
  }
  sku: {
    name: appServicePlanSku
  }
}

// App Service
resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: appName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'DOCKER|${containerRegistry.properties.loginServer}/${dockerImageName}:${dockerImageTag}'
      alwaysOn: appServicePlanSku != 'F1'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      scmMinTlsVersion: '1.2'
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_URL'
          value: 'https://${containerRegistry.properties.loginServer}'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_USERNAME'
          value: containerRegistry.listCredentials().username
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_PASSWORD'
          value: containerRegistry.listCredentials().passwords[0].value
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: azureOpenAiEndpoint
        }
        {
          name: 'AZURE_OPENAI_KEY'
          value: azureOpenAiKey
        }
        {
          name: 'AZURE_OPENAI_CHATGPT_DEPLOYMENT'
          value: azureOpenAiDeployment
        }
        {
          name: 'AZURE_OPENAI_API_VERSION'
          value: azureOpenAiApiVersion
        }
        {
          name: 'VECTOR_DB_PATH'
          value: '/tmp/resume_vectordb'
        }
        {
          name: 'PORT'
          value: '80'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: applicationInsights.properties.ConnectionString
        }
      ]
    }
    httpsOnly: true
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Configure logging
resource appServiceLogs 'Microsoft.Web/sites/config@2023-01-01' = {
  parent: appService
  name: 'logs'
  properties: {
    applicationLogs: {
      fileSystem: {
        level: 'Warning'
      }
    }
    httpLogs: {
      fileSystem: {
        retentionInMb: 35
        enabled: true
      }
    }
    detailedErrorMessages: {
      enabled: true
    }
    failedRequestsTracing: {
      enabled: true
    }
  }
}

// Outputs
output appServiceUrl string = 'https://${appService.properties.defaultHostName}'
output acrLoginServer string = containerRegistry.properties.loginServer
output acrName string = containerRegistry.name
output appName string = appService.name
output resourceGroupName string = resourceGroup().name