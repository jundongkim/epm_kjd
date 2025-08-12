'use client'

import { useState, useEffect } from 'react'
import { 
  Plus, 
  Settings, 
  Play, 
  Pause, 
  Edit, 
  Trash2, 
  TestTube, 
  CheckCircle, 
  XCircle, 
  Clock,
  Bot,
  Zap,
  Database,
  AlertCircle,
  Activity,
  Target,
  Server
} from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import { useDify } from '@/hooks/useDify'
import { CreateDifyServiceRequest, DifyServiceConfig } from '@/types/dify'

// ============================
// StatusCard 컴포넌트 (다른 페이지와 동일)
// ============================

interface StatusCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  trend?: string
  color: string
}

function StatusCard({ title, value, icon, trend, color }: StatusCardProps) {
  return (
    <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 hover:bg-muted/50 transition-all duration-300 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-muted-foreground text-sm mb-1">{title}</p>
          <p className="text-2xl font-bold text-foreground">{value}</p>
          {trend && (
            <p className={`text-sm ${trend.includes('↑') ? 'text-accent-cyan' : trend.includes('↓') ? 'text-accent-orange' : 'text-muted-foreground'}`}>
              {trend}
            </p>
          )}
        </div>
        <div 
          className="p-3 rounded-lg"
          style={{ backgroundColor: color }}
        >
          {icon}
        </div>
      </div>
    </div>
  )
}

export default function DifyServicePage() {
  const { t } = useTranslation()
  const {
    services,
    currentService,
    apps,
    isLoading,
    error,
    createService,
    updateService,
    deleteService,
    setActiveService,
    testService,
    fetchApps,
    createApp,
    clearError
  } = useDify()

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingService, setEditingService] = useState<DifyServiceConfig | null>(null)
  const [showAppForm, setShowAppForm] = useState(false)
  const [testResults, setTestResults] = useState<{ [key: string]: any }>({})

  const [serviceForm, setServiceForm] = useState<CreateDifyServiceRequest>({
    name: '',
    description: '',
    apiUrl: 'http://localhost:5001/v1',
    apiKey: ''
  })

  const [appForm, setAppForm] = useState({
    name: '',
    description: '',
    mode: 'chatbot' as const
  })

  useEffect(() => {
    if (currentService) {
      fetchApps()
    }
  }, [currentService, fetchApps])

  const handleCreateService = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createService(serviceForm)
      setServiceForm({
        name: '',
        description: '',
        apiUrl: 'http://localhost:5001/v1',
        apiKey: ''
      })
      setShowCreateForm(false)
    } catch (error) {
      console.error('Failed to create service:', error)
    }
  }

  const handleEditService = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingService) return

    try {
      await updateService({
        id: editingService.id,
        ...serviceForm
      })
      setEditingService(null)
      setShowCreateForm(false)
    } catch (error) {
      console.error('Failed to update service:', error)
    }
  }

  const handleTestConnection = async (service: DifyServiceConfig) => {
    setTestResults(prev => ({ ...prev, [service.id]: { testing: true } }))
    
    try {
      const result = await testService({
        name: service.name,
        description: service.description,
        apiUrl: service.apiUrl,
        apiKey: service.apiKey
      })
      
      setTestResults(prev => ({ ...prev, [service.id]: result }))
    } catch (error: any) {
      setTestResults(prev => ({ 
        ...prev, 
        [service.id]: { 
          success: false, 
          error: error.message 
        } 
      }))
    }
  }

  const handleCreateApp = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createApp(appForm)
      setAppForm({
        name: '',
        description: '',
        mode: 'chatbot'
      })
      setShowAppForm(false)
    } catch (error) {
      console.error('Failed to create app:', error)
    }
  }

  const startEdit = (service: DifyServiceConfig) => {
    setEditingService(service)
    setServiceForm({
      name: service.name,
      description: service.description || '',
      apiUrl: service.apiUrl,
      apiKey: service.apiKey
    })
    setShowCreateForm(true)
  }

  const cancelEdit = () => {
    setEditingService(null)
    setShowCreateForm(false)
    setServiceForm({
      name: '',
      description: '',
      apiUrl: 'http://localhost:5001/v1',
      apiKey: ''
    })
  }

  const getStatusIcon = (service: DifyServiceConfig) => {
    const result = testResults[service.id]
    
    if (result?.testing) return <Clock className="w-4 h-4 text-yellow-500 animate-spin" />
    if (result?.success) return <CheckCircle className="w-4 h-4 text-green-500" />
    if (result?.success === false) return <XCircle className="w-4 h-4 text-red-500" />
    if (service.isActive) return <Play className="w-4 h-4 text-blue-500" />
    return <Pause className="w-4 h-4 text-gray-400" />
  }

  return (
    <div className="p-6 space-y-8">
        {/* Header */}
      <div>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
                <Bot className="w-8 h-8 text-accent-blue" />
                {t('nav.aiAgent')}
              </h1>
              <p className="text-muted-foreground mt-2 text-lg">
                {t('difyService.subtitle')}
              </p>
            </div>
            <button
              onClick={() => setShowCreateForm(true)}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm"
            >
              <Plus className="w-5 h-5" />
              {t('difyService.buttons.addService')}
            </button>
          </div>
        </div>

        {/* Status Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatusCard
            title={t('difyService.statusCards.totalServices') || "등록된 서비스"}
            value={services.length}
            icon={<Server className="w-6 h-6 text-white" />}
            color="#3b82f6"
          />
          <StatusCard
            title={t('difyService.statusCards.activeServices') || "활성 서비스"}
            value={services.filter(s => s.isActive).length}
            icon={<Activity className="w-6 h-6 text-white" />}
            color="#22c55e"
          />
          <StatusCard
            title={t('difyService.statusCards.totalApps') || "총 앱 수"}
            value={apps.length}
            icon={<Bot className="w-6 h-6 text-white" />}
            color="#f97316"
          />
          <StatusCard
            title={t('difyService.statusCards.connectionStatus') || "연결 상태"}
            value={currentService ? (t('difyService.statusCards.connected') || "연결됨") : (t('difyService.statusCards.disconnected') || "미연결")}
            icon={<Target className="w-6 h-6 text-white" />}
            color={currentService ? "#22c55e" : "#ef4444"}
          />
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <div className="flex-1">
              <p className="text-red-700 dark:text-red-300 font-medium">{error.message}</p>
            </div>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700 dark:hover:text-red-300"
            >
              ×
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Services List */}
          <div className="lg:col-span-2">
            <div className="bg-card backdrop-blur-sm border border-border rounded-lg shadow-sm">
              <div className="p-6 border-b border-border">
                <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
                  <Settings className="w-5 h-5 text-accent-blue" />
                  {t('difyService.sections.serviceManagement')}
                </h2>
              </div>
              
              <div className="p-6">
                {services.length === 0 ? (
                  <div className="text-center py-16">
                    <div className="mb-6">
                      <div className="w-20 h-20 bg-gradient-primary rounded-full flex items-center justify-center mx-auto mb-4 opacity-60">
                        <Bot className="w-10 h-10 text-white" />
                      </div>
                    </div>
                    <h3 className="text-lg font-semibold text-foreground mb-2">{t('difyService.emptyStates.noServicesTitle') || "No Services Yet"}</h3>
                    <p className="text-muted-foreground mb-6">{t('difyService.messages.noServices')}</p>
                    <button
                      onClick={() => setShowCreateForm(true)}
                      className="px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm"
                    >
                      <Plus className="w-4 h-4 inline mr-2" />
                      {t('difyService.buttons.addService')}
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {services.map((service) => (
                      <div
                        key={service.id}
                        className={`p-6 border border-border rounded-lg transition-all duration-300 hover:bg-muted/50 hover:shadow-sm ${
                          service.isActive 
                            ? 'bg-accent-blue/5 border-accent-blue/30 shadow-sm' 
                            : 'bg-card backdrop-blur-sm'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            {getStatusIcon(service)}
                            <div>
                              <h3 className="font-medium text-foreground">{service.name}</h3>
                              <p className="text-sm text-muted-foreground">{service.description}</p>
                              <p className="text-xs text-muted-foreground mt-1">{service.apiUrl}</p>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            {testResults[service.id]?.success && (
                              <span className="text-xs text-green-600 dark:text-green-400">
                                {testResults[service.id].latency}ms | {testResults[service.id].appsCount} apps
                              </span>
                            )}
                            
                            <button
                              onClick={() => handleTestConnection(service)}
                              className="p-2 hover:bg-muted rounded-lg border border-border transition-all duration-300 hover:border-accent-blue/50 group"
                              title={t('difyService.buttons.testConnection')}
                            >
                              <TestTube className="w-4 h-4 text-muted-foreground group-hover:text-accent-blue transition-colors" />
                            </button>
                            
                            <button
                              onClick={() => startEdit(service)}
                              className="p-2 hover:bg-muted rounded-lg border border-border transition-all duration-300 hover:border-accent-yellow/50 group"
                              title={t('difyService.buttons.editService')}
                            >
                              <Edit className="w-4 h-4 text-muted-foreground group-hover:text-accent-yellow transition-colors" />
                            </button>
                            
                            <button
                              onClick={() => setActiveService(service.id)}
                              className="p-2 hover:bg-muted rounded-lg border border-border transition-all duration-300 hover:border-accent-green/50 group disabled:opacity-50 disabled:cursor-not-allowed"
                              title={service.isActive ? t('difyService.buttons.deactivate') : t('difyService.buttons.activate')}
                              disabled={service.isActive}
                            >
                              {service.isActive ? 
                                <Pause className="w-4 h-4 text-accent-green" /> : 
                                <Play className="w-4 h-4 text-muted-foreground group-hover:text-accent-green transition-colors" />
                              }
                            </button>
                            
                            <button
                              onClick={() => deleteService(service.id)}
                              className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg border border-border hover:border-red-300 dark:hover:border-red-700 transition-all duration-300 group"
                              title={t('difyService.buttons.deleteService')}
                            >
                              <Trash2 className="w-4 h-4 text-red-500 group-hover:text-red-600 transition-colors" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Apps Panel */}
          <div>
            <div className="bg-card backdrop-blur-sm border border-border rounded-lg shadow-sm">
              <div className="p-6 border-b border-border">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
                    <Database className="w-5 h-5 text-accent-green" />
                    {t('difyService.sections.appStore')}
                  </h2>
                  {currentService && (
                    <button
                      onClick={() => setShowAppForm(true)}
                      className="p-2 hover:bg-muted rounded-lg border border-border transition-all duration-300 hover:border-accent-green/50"
                      title={t('difyService.buttons.createApp')}
                    >
                      <Plus className="w-4 h-4 text-accent-green" />
                    </button>
                  )}
                </div>
              </div>
              
              <div className="p-6">
                {!currentService ? (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Settings className="w-8 h-8 text-muted-foreground" />
                    </div>
                    <h4 className="font-semibold text-foreground mb-2">{t('difyService.emptyStates.noActiveServiceTitle') || "No Active Service"}</h4>
                    <p className="text-sm text-muted-foreground">
                      {t('difyService.emptyStates.selectActiveService') || "Select an active service to view apps"}
                    </p>
                  </div>
                ) : apps.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 bg-accent-green/10 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Database className="w-8 h-8 text-accent-green" />
                    </div>
                    <h4 className="font-semibold text-foreground mb-2">{t('difyService.emptyStates.noAppsTitle') || "No Apps Found"}</h4>
                    <p className="text-sm text-muted-foreground mb-4">{t('difyService.messages.noApps')}</p>
                    <button
                      onClick={() => setShowAppForm(true)}
                      className="px-4 py-2 bg-accent-green hover:bg-accent-green/90 text-white font-medium rounded-lg transition-all duration-300 text-sm"
                    >
                      <Plus className="w-3 h-3 inline mr-1" />
                      {t('difyService.emptyStates.createFirstApp') || "Create First App"}
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {apps.map((app) => (
                      <div
                        key={app.id}
                        className="p-4 bg-card backdrop-blur-sm border border-border rounded-lg hover:bg-muted/50 transition-all duration-300 hover:shadow-sm group"
                      >
                        <div className="flex items-center gap-3">
                          <div className={`p-3 rounded-lg transition-all duration-300 group-hover:scale-110 ${
                            app.mode === 'chatbot' ? 'bg-blue-500 text-white' :
                            app.mode === 'agent' ? 'bg-green-500 text-white' :
                            'bg-purple-500 text-white'
                          }`}>
                            {app.mode === 'chatbot' ? <Bot className="w-5 h-5" /> :
                             app.mode === 'agent' ? <Zap className="w-5 h-5" /> :
                             <Settings className="w-5 h-5" />}
                          </div>
                          <div className="flex-1">
                            <h4 className="font-semibold text-sm text-foreground group-hover:text-accent-blue transition-colors">
                              {app.name}
                            </h4>
                            <p className="text-xs text-muted-foreground">
                              {t(`difyService.appTypes.${app.mode}`)}
                            </p>
                          </div>
                          <span className={`text-xs px-3 py-1 rounded-lg font-medium transition-all duration-300 ${
                            app.status === 'active' 
                              ? 'bg-green-100 dark:bg-green-900/20 text-green-600 border border-green-200 dark:border-green-800'
                              : 'bg-gray-100 dark:bg-gray-900/20 text-gray-600 border border-gray-200 dark:border-gray-800'
                          }`}>
                            {app.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Create/Edit Service Modal */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-card backdrop-blur-sm border border-border rounded-lg shadow-xl w-full max-w-md">
              <div className="p-6 border-b border-border">
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  {editingService ? (
                    <>
                      <Edit className="w-5 h-5 text-accent-blue" />
                      {t('difyService.buttons.editService')}
                    </>
                  ) : (
                    <>
                      <Plus className="w-5 h-5 text-accent-green" />
                      {t('difyService.buttons.addService')}
                    </>
                  )}
                </h3>
              </div>
              
              <form onSubmit={editingService ? handleEditService : handleCreateService} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    {t('difyService.serviceForm.name')}
                  </label>
                  <input
                    type="text"
                    value={serviceForm.name}
                    onChange={(e) => setServiceForm(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-4 py-3 border border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 transition-all duration-300"
                    placeholder={t('difyService.serviceForm.placeholders.name')}
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">
                    {t('difyService.serviceForm.description')}
                  </label>
                  <textarea
                    value={serviceForm.description}
                    onChange={(e) => setServiceForm(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-4 py-3 border border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 transition-all duration-300 resize-none"
                    placeholder={t('difyService.serviceForm.placeholders.description')}
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">
                    {t('difyService.serviceForm.apiUrl')}
                  </label>
                  <input
                    type="url"
                    value={serviceForm.apiUrl}
                    onChange={(e) => setServiceForm(prev => ({ ...prev, apiUrl: e.target.value }))}
                    className="w-full px-4 py-3 border border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 transition-all duration-300"
                    placeholder={t('difyService.serviceForm.placeholders.apiUrl')}
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">
                    {t('difyService.serviceForm.apiKey')}
                  </label>
                  <input
                    type="password"
                    value={serviceForm.apiKey}
                    onChange={(e) => setServiceForm(prev => ({ ...prev, apiKey: e.target.value }))}
                    className="w-full px-4 py-3 border border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 transition-all duration-300"
                    placeholder={t('difyService.serviceForm.placeholders.apiKey')}
                    required
                  />
                </div>
                
                <div className="flex gap-3 pt-6">
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="flex-1 px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (t('common.saving') || 'Saving...') : editingService ? (t('common.update') || 'Update') : (t('common.create') || 'Create')}
                  </button>
                  <button
                    type="button"
                    onClick={cancelEdit}
                    className="px-6 py-3 border border-border rounded-lg hover:bg-muted transition-all duration-300 text-foreground"
                  >
                    {t('common.cancel') || 'Cancel'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Create App Modal */}
        {showAppForm && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-card backdrop-blur-sm border border-border rounded-lg shadow-xl w-full max-w-md">
              <div className="p-6 border-b border-border">
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <Bot className="w-5 h-5 text-accent-purple" />
                  {t('difyService.buttons.createApp')}
                </h3>
              </div>
              
              <form onSubmit={handleCreateApp} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">{t('difyService.appForm.name') || "App Name"}</label>
                  <input
                    type="text"
                    value={appForm.name}
                    onChange={(e) => setAppForm(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-4 py-3 border border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 transition-all duration-300"
                    placeholder={t('difyService.appForm.placeholders.name') || "Enter app name"}
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">{t('difyService.appForm.description') || "Description"}</label>
                  <textarea
                    value={appForm.description}
                    onChange={(e) => setAppForm(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-4 py-3 border border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 transition-all duration-300 resize-none"
                    placeholder={t('difyService.appForm.placeholders.description') || "Enter app description"}
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">{t('difyService.appForm.type') || "App Type"}</label>
                  <select
                    value={appForm.mode}
                    onChange={(e) => setAppForm(prev => ({ ...prev, mode: e.target.value as any }))}
                    className="w-full px-4 py-3 border border-border rounded-lg bg-background text-foreground focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 transition-all duration-300"
                  >
                    <option value="chatbot">{t('difyService.appTypes.chatbot')}</option>
                    <option value="agent">{t('difyService.appTypes.agent')}</option>
                    <option value="workflow">{t('difyService.appTypes.workflow')}</option>
                  </select>
                </div>
                
                <div className="flex gap-3 pt-6">
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="flex-1 px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (t('common.creating') || 'Creating...') : (t('difyService.buttons.createApp') || 'Create App')}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAppForm(false)}
                    className="px-6 py-3 border border-border rounded-lg hover:bg-muted transition-all duration-300 text-foreground"
                  >
                    {t('common.cancel') || 'Cancel'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
    </div>
  )
} 