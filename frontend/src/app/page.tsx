'use client'

import Link from 'next/link'
import { Mail, CheckCircle, BookOpen, Brain, Microscope, Bot, Settings, DollarSign, FileText, Workflow, Zap } from 'lucide-react'
import AnimatedBackground from '@/components/AnimatedBackground'
import Navigation from '@/components/Navigation'
import HeroSection from '@/components/HeroSection'
import FeatureCard from '@/components/FeatureCard'
import { FloatingChatbot } from '@/components/FloatingChatbot'
import { FeatureCard as FeatureCardType } from '@/types'
import { useTranslation } from '@/hooks/useTranslation'

const getFeatures = (t: (key: string) => any, tArray: (key: string) => string[]): FeatureCardType[] => [
  {
    icon: <Brain className="w-12 h-12 text-accent-blue" />,
    title: t('features.dataGeneration.title'),
    description: t('features.dataGeneration.description'),
    benefits: tArray('features.dataGeneration.benefits'),
    tech: tArray('features.dataGeneration.tech')
  },
  {
    icon: <Microscope className="w-12 h-12 text-accent-purple" />,
    title: t('features.experimentDesign.title'),
    description: t('features.experimentDesign.description'),
    benefits: tArray('features.experimentDesign.benefits'),
    tech: tArray('features.experimentDesign.tech')
  },
  {
    icon: <Bot className="w-12 h-12 text-accent-cyan" />,
    title: t('features.productModeling.title'),
    description: t('features.productModeling.description'),
    benefits: tArray('features.productModeling.benefits'),
    tech: tArray('features.productModeling.tech')
  },
  {
    icon: <Settings className="w-12 h-12 text-accent-orange" />,
    title: t('features.processAnalysis.title'),
    description: t('features.processAnalysis.description'),
    benefits: tArray('features.processAnalysis.benefits'),
    tech: tArray('features.processAnalysis.tech')
  },
  {
    icon: <DollarSign className="w-12 h-12 text-accent-green" />,
    title: t('features.costManagement.title'),
    description: t('features.costManagement.description'),
    benefits: tArray('features.costManagement.benefits'),
    tech: tArray('features.costManagement.tech')
  },
  {
    icon: <FileText className="w-12 h-12 text-accent-pink" />,
    title: t('features.aiReport.title'),
    description: t('features.aiReport.description'),
    benefits: tArray('features.aiReport.benefits'),
    tech: tArray('features.aiReport.tech')
  },
  {
    icon: <Workflow className="w-12 h-12 text-accent-indigo" />,
    title: t('features.workflow.title'),
    description: t('features.workflow.description'),
    benefits: tArray('features.workflow.benefits'),
    tech: tArray('features.workflow.tech')
  },
  {
    icon: <Zap className="w-12 h-12 text-accent-yellow" />,
    title: t('features.aiAgent.title'),
    description: t('features.aiAgent.description'),
    benefits: tArray('features.aiAgent.benefits'),
    tech: tArray('features.aiAgent.tech')
  }
]

const getTechStacks = (t: (key: string) => any): Array<{category: string, items: string[]}> => {
  const techStack = t('techStack.categories')
  return [
    {
      category: techStack.aiml.title,
      items: techStack.aiml.items
    },
    {
      category: techStack.optimization.title,
      items: techStack.optimization.items
    },
    {
      category: techStack.platform.title,
      items: techStack.platform.items
    },
    {
      category: techStack.algorithms.title,
      items: techStack.algorithms.items
    },
    {
      category: techStack.automation.title,
      items: techStack.automation.items
    },
    {
      category: techStack.integration.title,
      items: techStack.integration.items
    }
  ]
}

export default function Home() {
  const { t, tArray } = useTranslation()
  const features = getFeatures(t, tArray)
  const techStacks = getTechStacks(t)
  
  return (
    <div className="min-h-screen font-paperlogy">
      <AnimatedBackground />
      <Navigation />
      
      <main>
        <HeroSection />
        
        {/* Features Section */}
        <section id="features" className="py-20 px-4">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16 animate-fade-in-up">
              <h2 className="text-4xl md:text-5xl font-black text-foreground mb-6">
                <span className="gradient-text">{t('features.title')}</span>
              </h2>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
                {t('features.subtitle')}
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
              {features.map((feature, index) => (
                <FeatureCard key={index} feature={feature} index={index} />
              ))}
            </div>
          </div>
        </section>

        {/* Tech Stack Section */}
        <section id="tech" className="py-20 px-4">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16 animate-fade-in-up">
              <h2 className="text-4xl md:text-5xl font-black text-foreground mb-6">
                <span className="gradient-text">{t('techStack.title')}</span>
              </h2>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
                {t('techStack.subtitle')}
              </p>
            </div>
            
                         <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
               {techStacks.map((stack, index) => (
                 <div 
                   key={index} 
                   className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 hover:bg-muted/50 transition-all duration-300 hover:scale-105 animate-fade-in-up shadow-sm"
                   style={{ animationDelay: `${index * 0.1}s` }}
                 >
                  <h3 className="text-xl font-bold text-foreground mb-4 gradient-text">{stack.category}</h3>
                  <ul className="space-y-2">
                    {stack.items.map((item: string, i: number) => (
                      <li key={i} className="text-muted-foreground text-sm hover:text-foreground transition-colors duration-200 flex items-center">
                        <div className="w-2 h-2 bg-gradient-primary rounded-full mr-3 opacity-60"></div>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Contact Section */}
        <section id="contact" className="py-20 px-4">
                     <div className="max-w-4xl mx-auto text-center">
             <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-12 shadow-sm hover:shadow-md transition-all duration-300 animate-fade-in-up">
              <h2 className="text-4xl font-black text-foreground mb-8">
                <span className="gradient-text">{t('contact.title')}</span>
              </h2>
              
              <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
                {t('contact.subtitle')}
              </p>
              
                             <div className="flex flex-col sm:flex-row gap-6 justify-center mb-8">
                 <Link href="/copilot/data-generation" className="flex items-center justify-center px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm group">
                   <span>{t('contact.requestDemo')}</span>
                   <svg className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                   </svg>
                 </Link>
                 <Link href="#contact" className="flex items-center justify-center px-6 py-3 bg-card hover:bg-muted/50 border border-border text-foreground font-semibold rounded-lg transition-all duration-300 shadow-sm group">
                   <span>{t('contact.contactSales')}</span>
                   <Mail className="w-5 h-5 ml-2 group-hover:scale-110 transition-transform duration-300" />
                 </Link>
               </div>
              
              <div className="grid md:grid-cols-3 gap-8 text-foreground">
                                 <div className="group">
                   <div className="w-12 h-12 bg-gradient-primary rounded-lg flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300">
                    <Mail className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-bold mb-2">{t('contact.emailSupport.title')}</h3>
                  <p className="text-sm">{t('contact.emailSupport.email')}</p>
                  <p className="text-xs text-muted-foreground mt-1">{t('contact.emailSupport.description')}</p>
                </div>
                
                                 <div className="group">
                   <div className="w-12 h-12 bg-gradient-secondary rounded-lg flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300">
                    <CheckCircle className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-bold mb-2">{t('contact.systemStatus.title')}</h3>
                  <p className="text-sm text-green-400">{t('contact.systemStatus.status')}</p>
                  <p className="text-xs text-muted-foreground mt-1">{t('contact.systemStatus.description')}</p>
                </div>
                
                                 <div className="group">
                   <div className="w-12 h-12 bg-gradient-accent rounded-lg flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300">
                    <BookOpen className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-bold mb-2">{t('contact.documentation.title')}</h3>
                  <p className="text-sm">{t('contact.documentation.description')}</p>
                  <p className="text-xs text-muted-foreground mt-1">{t('contact.documentation.subDescription')}</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
      
             <footer className="py-12 px-4 border-t border-border bg-card backdrop-blur-sm">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <h3 className="text-lg font-bold text-foreground mb-4">Product</h3>
              <ul className="space-y-2">
                <li><Link href="/aiadvisor" className="text-muted-foreground hover:text-foreground transition-colors">AI Advisor</Link></li>
                <li><Link href="/copilot/data-generation" className="text-muted-foreground hover:text-foreground transition-colors">Data Generation</Link></li>
                <li><Link href="/copilot/experiment-design" className="text-muted-foreground hover:text-foreground transition-colors">Experiment Design</Link></li>
                <li><Link href="/copilot/product-modeling" className="text-muted-foreground hover:text-foreground transition-colors">Product Modeling</Link></li>
                <li><Link href="/copilot/process-analysis" className="text-muted-foreground hover:text-foreground transition-colors">Process Analysis</Link></li>
                <li><Link href="/copilot/cost-management" className="text-muted-foreground hover:text-foreground transition-colors">Cost Management</Link></li>
                <li><Link href="/copilot/ai-report" className="text-muted-foreground hover:text-foreground transition-colors">AI Reports</Link></li>
                <li><Link href="/copilot/workflow" className="text-muted-foreground hover:text-foreground transition-colors">Workflow</Link></li>
                <li><Link href="/copilot/ai-agent" className="text-muted-foreground hover:text-foreground transition-colors">AI Agent</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-bold text-foreground mb-4">Features</h3>
              <ul className="space-y-2">
                <li><span className="text-muted-foreground">ML Model Training</span></li>
                <li><span className="text-muted-foreground">Real-time Analytics</span></li>
                <li><span className="text-muted-foreground">DOE & Bayesian Optimization</span></li>
                <li><span className="text-muted-foreground">Workflow Automation</span></li>
                <li><span className="text-muted-foreground">AI Agent Integration</span></li>
                <li><span className="text-muted-foreground">Cost Optimization</span></li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-bold text-foreground mb-4">Company</h3>
              <ul className="space-y-2">
                <li><a href="#contact" className="text-muted-foreground hover:text-foreground transition-colors">About Us</a></li>
                <li><a href="#contact" className="text-muted-foreground hover:text-foreground transition-colors">Contact</a></li>
                <li><a href="#" className="text-muted-foreground hover:text-foreground transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="text-muted-foreground hover:text-foreground transition-colors">Terms of Service</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-bold text-foreground mb-4">Connect</h3>
              <ul className="space-y-2">
                <li><span className="text-muted-foreground">support@dx-ai.com</span></li>
                <li><span className="text-muted-foreground">+1 (555) 123-4567</span></li>
                <li><span className="text-muted-foreground">24/7 Support</span></li>
                <li><span className="text-accent-blue">🟢 System Online</span></li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t border-border text-center text-muted-foreground">
            <p>&copy; 2025 DX-AI Manufacturing Copilot. All rights reserved. | Built with Next.js & FastAPI</p>
          </div>
        </div>
      </footer>
      
      {/* AI 챗봇 위젯 */}
      <FloatingChatbot 
        topic="general" 
        sessionId="landing_page_chat"
        position="bottom-right"
        theme="dark"
        accentColor="blue"
        maxHeight={800}
        width={600}
        showSessionInfo={false}
      />
    </div>
  )
}
