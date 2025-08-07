export interface FeatureCard {
  icon: string | React.ReactNode
  title: string
  description: string
  benefits: string[]
  tech: string[]
}

export interface Metric {
  label: string
  value: string
  delta?: string
  trend?: 'up' | 'down' | 'neutral'
}

export interface TechStack {
  category: string
  items: string[]
}

export interface NavigationItem {
  id: string
  label: string
  href: string
}

export interface ContactInfo {
  type: 'email' | 'phone' | 'address'
  label: string
  value: string
  icon: string
}

export interface TeamMember {
  name: string
  role: string
  image: string
  bio: string
} 