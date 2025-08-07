'use client'

import { useState } from 'react'
import { 
  Play, 
  Loader2, 
  CheckCircle, 
  AlertCircle, 
  Database, 
  Factory, 
  Beaker,
  Calculator
} from 'lucide-react'
import { ReactNode } from 'react'
import { 
  useDataGeneration, 
  useProcessAnalysis, 
  useExperimentDesign, 
  useCostAnalysis,
  useSystemStatus
} from '@/hooks/useApi'
import { useTranslation } from '@/hooks/useTranslation'

interface DemoItem {
  id: string;
  titleKey: string;
  descriptionKey: string;
  icon: ReactNode;
  color: string;
  hook: any;
  sampleData: any;
}

export default function ApiDemo() {
  const [activeDemo, setActiveDemo] = useState<string | null>(null)
  const { t } = useTranslation()
  
  const systemStatus = useSystemStatus()
  const dataGeneration = useDataGeneration()
  const processAnalysis = useProcessAnalysis()
  const experimentDesign = useExperimentDesign()
  const costAnalysis = useCostAnalysis()

  const demos: DemoItem[] = [
    {
      id: 'system-status',
      titleKey: 'apiDemo.systemStatus.title',
      descriptionKey: 'apiDemo.systemStatus.description',
      icon: <CheckCircle className="w-6 h-6" />,
      color: 'bg-green-500',
      hook: systemStatus,
      sampleData: null
    },
    {
      id: 'data-generation',
      titleKey: 'apiDemo.dataGeneration.title',
      descriptionKey: 'apiDemo.dataGeneration.description',
      icon: <Database className="w-6 h-6" />,
      color: 'bg-blue-500',
      hook: dataGeneration,
      sampleData: {
        num_samples: 100,
        product_type: "전자부품",
        parameters: {
          temperature_range: [150, 200],
          pressure_range: [2.0, 3.0],
          quality_target: 95
        }
      }
    },
    {
      id: 'process-analysis',
      titleKey: 'apiDemo.processAnalysis.title',
      descriptionKey: 'apiDemo.processAnalysis.description',
      icon: <Factory className="w-6 h-6" />,
      color: 'bg-purple-500',
      hook: processAnalysis,
      sampleData: {
        process_data: {
          temperature: 175,
          pressure: 2.5,
          flow_rate: 200,
          yield: 85,
          quality: 92
        },
        analysis_type: "performance"
      }
    },
    {
      id: 'experiment-design',
      titleKey: 'apiDemo.experimentDesign.title',
      descriptionKey: 'apiDemo.experimentDesign.description',
      icon: <Beaker className="w-6 h-6" />,
      color: 'bg-orange-500',
      hook: experimentDesign,
      sampleData: {
        factors: [
          { name: "온도", min: 150, max: 200, unit: "°C" },
          { name: "압력", min: 2.0, max: 3.0, unit: "bar" },
          { name: "유량", min: 180, max: 220, unit: "L/min" }
        ],
        responses: ["수율", "품질", "원가"],
        design_type: "factorial"
      }
    },
    {
      id: 'cost-analysis',
      titleKey: 'apiDemo.costAnalysis.title',
      descriptionKey: 'apiDemo.costAnalysis.description',
      icon: <Calculator className="w-6 h-6" />,
      color: 'bg-green-600',
      hook: costAnalysis,
      sampleData: {
        cost_data: {
          material_a: 10000,
          material_b: 5000,
          labor_cost: 20000,
          energy_cost: 3000,
          overhead: 8000
        },
        analysis_type: "basic"
      }
    }
  ]

  const handleDemo = async (demo: any) => {
    setActiveDemo(demo.id)
    
    try {
      if (demo.sampleData) {
        await demo.hook.execute(demo.sampleData)
      } else {
        await demo.hook.execute()
      }
    } catch (error) {
      console.error('Demo execution error:', error)
    } finally {
      setActiveDemo(null)
    }
  }

  return (
    <section className="py-20 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-foreground mb-6">
            {t('apiDemo.title')}
          </h2>
          <p className="text-xl text-muted-foreground">
            {t('apiDemo.description')}
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {demos.map((demo) => (
            <div 
              key={demo.id}
              className="bg-glass-card backdrop-blur-glass-card border border-white/20 rounded-glass-card p-6 hover:bg-glass-300 transition-all duration-300 hover:-translate-y-2"
            >
              <div className="flex items-center gap-4 mb-4">
                <div className={`p-3 rounded-xl ${demo.color} text-white`}>
                  {demo.icon}
                </div>
                <div>
                  <h3 className="text-xl font-bold text-foreground">{t(demo.titleKey)}</h3>
                </div>
              </div>
              
              <p className="text-muted-foreground mb-6 text-sm leading-relaxed">
                {t(demo.descriptionKey)}
              </p>

              <button
                onClick={() => handleDemo(demo)}
                disabled={activeDemo === demo.id || demo.hook.loading}
                className={`w-full py-3 px-4 rounded-xl font-medium transition-all duration-300 flex items-center justify-center gap-2 ${
                  activeDemo === demo.id || demo.hook.loading
                    ? 'bg-muted cursor-not-allowed text-muted-foreground'
                    : 'bg-primary hover:bg-primary/90 text-white'
                }`}
              >
                {activeDemo === demo.id || demo.hook.loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Play className="w-5 h-5" />
                )}
                {activeDemo === demo.id || demo.hook.loading ? t('apiDemo.executing') : t('apiDemo.execute')}
              </button>

              {/* 결과 표시 */}
              {demo.hook.data && (
                <div className="mt-4 p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                  <div className="flex items-center gap-2 text-green-400 text-sm font-medium mb-2">
                    <CheckCircle className="w-4 h-4" />
                    {t('apiDemo.success')}
                  </div>
                  <pre className="text-xs text-muted-foreground overflow-x-auto">
                    {JSON.stringify(demo.hook.data, null, 2)}
                  </pre>
                </div>
              )}

              {/* 에러 표시 */}
              {demo.hook.error && (
                <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <div className="flex items-center gap-2 text-red-400 text-sm font-medium mb-2">
                    <AlertCircle className="w-4 h-4" />
                    {t('apiDemo.failed')}
                  </div>
                  <p className="text-xs text-red-400">{demo.hook.error}</p>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 연결 상태 표시 */}
        <div className="mt-16 text-center">
          <div className="bg-glass-card backdrop-blur-glass-card border border-white/20 rounded-glass-card p-6 inline-block">
            <h3 className="text-lg font-bold text-foreground mb-4">{t('apiDemo.connectionStatus')}</h3>
            <div className="text-sm text-muted-foreground">
              FastAPI 서버: <span className="text-primary">http://localhost:8000</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
} 