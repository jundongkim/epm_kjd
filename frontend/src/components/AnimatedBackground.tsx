'use client'

import { useEffect, useState, useRef } from 'react'

interface ParticleProps {
  x: number
  y: number
  size: number
  speed: number
  direction: number
  opacity: number
  color: string
  type: 'circle' | 'square' | 'triangle'
}

export default function AnimatedBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [mounted, setMounted] = useState(false)
  const animationRef = useRef<number | undefined>(undefined)

  useEffect(() => {
    setMounted(true)
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    // Create particles
    const createParticles = () => {
      const particleCount = Math.min(window.innerWidth / 30, 30)
      const newParticles: ParticleProps[] = []
      
      const colors = ['#4a90e2', '#6c5ce7', '#00b894', '#fd79a8', '#e17055']
      const types: ('circle' | 'square' | 'triangle')[] = ['circle', 'square', 'triangle']
      
      for (let i = 0; i < particleCount; i++) {
        newParticles.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          size: Math.random() * 4 + 1,
          speed: Math.random() * 1 + 0.2,
          direction: Math.random() * Math.PI * 2,
          opacity: Math.random() * 0.2 + 0.05,
          color: colors[Math.floor(Math.random() * colors.length)],
          type: types[Math.floor(Math.random() * types.length)],
        })
      }
      return newParticles
    }

    let currentParticles = createParticles()

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      // Update particles
      currentParticles = currentParticles.map(particle => {
        // Update position
        particle.x += Math.cos(particle.direction) * particle.speed
        particle.y += Math.sin(particle.direction) * particle.speed
        
        // Bounce off edges
        if (particle.x < 0 || particle.x > canvas.width) {
          particle.direction = Math.PI - particle.direction
        }
        if (particle.y < 0 || particle.y > canvas.height) {
          particle.direction = -particle.direction
        }
        
        // Keep particles within bounds
        particle.x = Math.max(0, Math.min(canvas.width, particle.x))
        particle.y = Math.max(0, Math.min(canvas.height, particle.y))
        
        // Slight opacity variation
        particle.opacity = Math.max(0.1, Math.min(0.7, particle.opacity + (Math.random() - 0.5) * 0.02))
        
        return particle
      })
      
      // Draw particles
      currentParticles.forEach(particle => {
        ctx.save()
        ctx.globalAlpha = particle.opacity
        ctx.fillStyle = particle.color
        ctx.shadowBlur = 20
        ctx.shadowColor = particle.color
        
        switch (particle.type) {
          case 'circle':
            ctx.beginPath()
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2)
            ctx.fill()
            break
          case 'square':
            ctx.fillRect(particle.x - particle.size, particle.y - particle.size, particle.size * 2, particle.size * 2)
            break
          case 'triangle':
            ctx.beginPath()
            ctx.moveTo(particle.x, particle.y - particle.size)
            ctx.lineTo(particle.x - particle.size, particle.y + particle.size)
            ctx.lineTo(particle.x + particle.size, particle.y + particle.size)
            ctx.closePath()
            ctx.fill()
            break
        }
        ctx.restore()
      })
      
      // Draw connections between nearby particles
      currentParticles.forEach((particle, i) => {
        currentParticles.slice(i + 1).forEach(otherParticle => {
          const dx = particle.x - otherParticle.x
          const dy = particle.y - otherParticle.y
          const distance = Math.sqrt(dx * dx + dy * dy)
          
          if (distance < 120) {
            ctx.save()
            ctx.globalAlpha = (120 - distance) / 120 * 0.2
            ctx.strokeStyle = particle.color
            ctx.lineWidth = 1
            ctx.beginPath()
            ctx.moveTo(particle.x, particle.y)
            ctx.lineTo(otherParticle.x, otherParticle.y)
            ctx.stroke()
            ctx.restore()
          }
        })
      })
      
      animationRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      window.removeEventListener('resize', resizeCanvas)
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [])

  if (!mounted) return null

  return (
    <>
      {/* Canvas for particle animation */}
      <canvas
        ref={canvasRef}
        className="fixed inset-0 -z-20 pointer-events-none"
        style={{ background: 'transparent' }}
      />
      
      {/* Static gradient shapes */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        {/* Large gradient orbs */}
        <div className="absolute -top-64 -right-64 w-128 h-128 bg-gradient-to-br from-accent-blue/10 via-accent-purple/10 to-transparent rounded-full blur-3xl animate-pulse opacity-30" />
        <div className="absolute -bottom-64 -left-64 w-128 h-128 bg-gradient-to-tr from-accent-cyan/10 via-accent-pink/10 to-transparent rounded-full blur-3xl animate-pulse opacity-30" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-r from-accent-purple/5 to-accent-blue/5 rounded-full blur-3xl animate-spin-slow opacity-20" />
        
        {/* Grid pattern */}
        <div 
          className="absolute inset-0 opacity-2"
          style={{
            backgroundImage: `
              linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)
            `,
            backgroundSize: '60px 60px'
          }}
        />
        
        {/* Floating geometric shapes */}
        <div className="absolute top-20 left-20 w-6 h-6 bg-accent-blue/20 rounded-full animate-float opacity-40" />
        <div className="absolute top-40 right-40 w-4 h-4 bg-accent-purple/20 rotate-45 animate-float opacity-40" style={{ animationDelay: '1s' }} />
        <div className="absolute bottom-40 left-40 w-3 h-3 bg-accent-cyan/20 rounded-full animate-float opacity-40" style={{ animationDelay: '2s' }} />
        <div className="absolute bottom-20 right-20 w-4 h-4 bg-accent-pink/20 rotate-45 animate-float opacity-40" style={{ animationDelay: '3s' }} />
        
        {/* Animated gradient lines - More Subtle */}
        <div className="absolute top-0 left-1/4 w-px h-full bg-gradient-to-b from-transparent via-accent-blue/10 to-transparent animate-ping-slow opacity-30" />
        <div className="absolute top-0 right-1/4 w-px h-full bg-gradient-to-b from-transparent via-accent-purple/10 to-transparent animate-ping-slow opacity-30" style={{ animationDelay: '1s' }} />
        <div className="absolute left-0 top-1/4 w-full h-px bg-gradient-to-r from-transparent via-accent-cyan/10 to-transparent animate-ping-slow opacity-30" style={{ animationDelay: '2s' }} />
        <div className="absolute left-0 bottom-1/4 w-full h-px bg-gradient-to-r from-transparent via-accent-pink/10 to-transparent animate-ping-slow opacity-30" style={{ animationDelay: '3s' }} />
        
        {/* Radial gradient overlay */}
        <div className="absolute inset-0 bg-gradient-radial from-transparent via-transparent to-dark-950/30" />
      </div>
    </>
  )
} 