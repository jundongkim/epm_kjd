'use client'

import React from 'react'
import Link from 'next/link'
import { ChevronRight, Zap, TrendingUp, ArrowUpRight } from 'lucide-react'
import { FeatureCard as FeatureCardType } from '@/types'
import { useTranslation } from '@/hooks/useTranslation'

interface FeatureCardProps {
  feature: FeatureCardType
  index: number
}

export default function FeatureCard({ feature, index }: FeatureCardProps) {
  const { t } = useTranslation()

  // Map feature titles to routes
  const getFeatureRoute = (title: string) => {
    const routeMap: { [key: string]: string } = {
      // 한국어 제목
      "데이터 생성": "/copilot/data-generation",
      "공정 분석": "/copilot/process-analysis", 
      "실험 설계": "/copilot/experiment-design",
      "모델링": "/copilot/product-modeling",
      "비용 관리": "/copilot/cost-management",
      "AI 보고서": "/copilot/ai-report",
      // 영어 제목
      "Data Generation": "/copilot/data-generation",
      "Process Analysis": "/copilot/process-analysis",
      "Experiment Design": "/copilot/experiment-design", 
      "Product Modeling": "/copilot/product-modeling",
      "Cost Management": "/copilot/cost-management",
      "AI Report": "/copilot/ai-report"
    }
    return routeMap[title] || "/copilot/data-generation"
  }

  const featureRoute = getFeatureRoute(feature.title)

  return (
          <div 
        className="group relative overflow-hidden bg-card backdrop-blur-sm border border-border rounded-lg p-6 hover:bg-muted/50 transition-all duration-500 hover:shadow-sm hover:scale-[1.02] animate-fade-in-up"
        style={{ animationDelay: `${index * 0.1}s` }}
      >
      {/* Gradient overlay on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-accent-blue/5 via-accent-purple/5 to-accent-cyan/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      
      {/* Icon background glow */}
      <div className="absolute -top-6 -right-6 w-24 h-24 bg-gradient-primary rounded-full opacity-0 group-hover:opacity-20 blur-2xl transition-opacity duration-500" />
      
      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="relative">
            <div className={`mb-3 group-hover:scale-110 transition-transform duration-300 ${typeof feature.icon === 'string' ? 'text-4xl' : ''}`}>
              {feature.icon}
            </div>
            <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-gradient-primary rounded-full opacity-0 group-hover:opacity-100 animate-pulse-glow transition-opacity duration-300">
              <Zap className="w-3 h-3 text-white absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
            </div>
          </div>
                     <div className="p-2 rounded-lg bg-muted/30 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <ArrowUpRight className="w-4 h-4 text-accent-blue" />
          </div>
        </div>

        {/* Title */}
        <h3 className="text-xl font-bold text-foreground mb-3 group-hover:text-transparent group-hover:bg-gradient-primary group-hover:bg-clip-text transition-all duration-300">
          {feature.title}
        </h3>

        {/* Description */}
        <p className="text-muted-foreground mb-4 text-sm leading-relaxed group-hover:text-foreground transition-colors duration-300">
          {feature.description}
        </p>

        {/* Benefits */}
        <div className="space-y-2 mb-5">
          {feature.benefits.map((benefit, i) => (
            <div 
              key={i} 
              className="flex items-start space-x-2 group/benefit"
              style={{ animationDelay: `${(index * 0.1) + (i * 0.05)}s` }}
            >
              <div className="relative mt-0.5">
                <div className="w-4 h-4 bg-gradient-primary rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <ChevronRight className="w-2.5 h-2.5 text-white" />
                </div>
                <div className="absolute inset-0 bg-gradient-primary rounded-full opacity-0 group-hover:opacity-50 blur-sm transition-opacity duration-300" />
              </div>
              <span className="text-muted-foreground text-xs group-hover:text-foreground transition-colors duration-300">
                {benefit}
              </span>
            </div>
          ))}
        </div>

        {/* Tech Stack */}
        <div className="space-y-2 mb-4">
          <div className="flex items-center space-x-2 mb-2">
            <TrendingUp className="w-3 h-3 text-accent-cyan" />
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Technology Stack
            </span>
          </div>
                     <div className="flex flex-wrap gap-1.5">
             {feature.tech.map((tech, i) => (
               <div
                 key={i}
                 className="px-2 py-0.5 bg-muted/50 border border-border rounded-lg text-xs font-medium text-muted-foreground hover:bg-accent-blue/10 hover:text-accent-blue transition-all duration-300 hover:scale-105"
                 style={{ animationDelay: `${(index * 0.1) + (i * 0.02)}s` }}
               >
                 {tech}
               </div>
             ))}
           </div>
        </div>

        {/* Action Button */}
                 <Link href={featureRoute} className="w-full flex items-center justify-center px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm group/btn">
          <span className="group-hover/btn:text-white transition-colors duration-300 text-sm">
            {t('common.view')}
          </span>
          <ChevronRight className="w-4 h-4 ml-2 group-hover/btn:translate-x-1 transition-transform duration-300" />
        </Link>
      </div>

             {/* Hover effect - animated border */}
       <div className="absolute inset-0 rounded-lg border border-transparent group-hover:border-accent-blue/30 transition-all duration-500">
         <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-accent-blue/20 via-accent-purple/20 to-accent-cyan/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-sm" />
       </div>
    </div>
  )
} 