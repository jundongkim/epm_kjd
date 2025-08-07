import * as React from 'react'
import { Brain, Microscope, Bot, Settings, DollarSign, FileText, Database, Cloud, Code, Zap, BarChart } from 'lucide-react'
import { FeatureCard as FeatureCardType } from '@/types'

export const getFeatures = (t: (key: string) => unknown, tArray: (key: string) => string[]): FeatureCardType[] => [
  {
    icon: React.createElement(Brain, { className: "w-12 h-12 text-accent-blue" }),
    title: t('features.dataGeneration.title') as string,
    description: t('features.dataGeneration.description') as string,
    benefits: tArray('features.dataGeneration.benefits'),
    tech: tArray('features.dataGeneration.tech')
  },
  {
    icon: React.createElement(Microscope, { className: "w-12 h-12 text-accent-purple" }),
    title: t('features.experimentDesign.title') as string,
    description: t('features.experimentDesign.description') as string,
    benefits: tArray('features.experimentDesign.benefits'),
    tech: tArray('features.experimentDesign.tech')
  },
  {
    icon: React.createElement(Bot, { className: "w-12 h-12 text-accent-cyan" }),
    title: t('features.productModeling.title') as string,
    description: t('features.productModeling.description') as string,
    benefits: tArray('features.productModeling.benefits'),
    tech: tArray('features.productModeling.tech')
  },
  {
    icon: React.createElement(Settings, { className: "w-12 h-12 text-accent-orange" }),
    title: t('features.processAnalysis.title') as string,
    description: t('features.processAnalysis.description') as string,
    benefits: tArray('features.processAnalysis.benefits'),
    tech: tArray('features.processAnalysis.tech')
  },
  {
    icon: React.createElement(DollarSign, { className: "w-12 h-12 text-accent-green" }),
    title: t('features.costManagement.title') as string,
    description: t('features.costManagement.description') as string,
    benefits: tArray('features.costManagement.benefits'),
    tech: tArray('features.costManagement.tech')
  },
  {
    icon: React.createElement(FileText, { className: "w-12 h-12 text-accent-pink" }),
    title: t('features.aiReport.title') as string,
    description: t('features.aiReport.description') as string,
    benefits: tArray('features.aiReport.benefits'),
    tech: tArray('features.aiReport.tech')
  }
]

export interface TechStackItem {
  icon: React.ReactNode
  title: string
  description: string
  tech: string[]
}

export const getTechStacks = (t: (key: string) => unknown, _: (key: string) => string[]): TechStackItem[] => {
  const techStack = t('techStack.categories') as Record<string, {
    title: string;
    description: string;
    items: string[];
  }>
  return [
    {
      icon: React.createElement(Brain, { className: "w-8 h-8" }),
      title: techStack.aiml.title,
      description: techStack.aiml.description,
      tech: techStack.aiml.items
    },
    {
      icon: React.createElement(BarChart, { className: "w-8 h-8" }),
      title: techStack.optimization.title,
      description: techStack.optimization.description,
      tech: techStack.optimization.items
    },
    {
      icon: React.createElement(Cloud, { className: "w-8 h-8" }),
      title: techStack.platform.title,
      description: techStack.platform.description,
      tech: techStack.platform.items
    },
    {
      icon: React.createElement(Code, { className: "w-8 h-8" }),
      title: techStack.algorithms.title,
      description: techStack.algorithms.description,
      tech: techStack.algorithms.items
    },
    {
      icon: React.createElement(Database, { className: "w-8 h-8" }),
      title: techStack.data.title,
      description: techStack.data.description,
      tech: techStack.data.items
    },
    {
      icon: React.createElement(Zap, { className: "w-8 h-8" }),
      title: techStack.realtime.title,
      description: techStack.realtime.description,
      tech: techStack.realtime.items
    }
  ]
} 