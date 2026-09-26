import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  GitBranch,
  Workflow,
  AlertTriangle,
  FileText,
  Settings,
  Zap,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useBackendStatus } from '@/hooks/useBackendStatus'

const navItems = [
  { label: 'Dashboard',    to: '/',             icon: LayoutDashboard },
  { label: 'Repositories', to: '/repositories', icon: GitBranch },
  { label: 'Workflow',     to: '/workflow',      icon: Workflow },
  { label: 'Findings',     to: '/findings',      icon: AlertTriangle },
  { label: 'Reports',      to: '/reports',       icon: FileText },
]

const statusDot: Record<string, string> = {
  checking: 'bg-amber-500 animate-pulse',
  online:   'bg-success',
  offline:  'bg-error',
}

const statusLabel: Record<string, string> = {
  checking: 'Connecting...',
  online:   'Connected',
  offline:  'Offline',
}

export function Sidebar() {
  const { status } = useBackendStatus()

  return (
    <aside className="w-56 shrink-0 border-r border-border bg-card flex flex-col h-full">
      {/* Brand */}
      <div className="h-14 flex items-center gap-2.5 px-4 border-b border-border">
        <div className="flex items-center justify-center w-7 h-7 rounded-md bg-primary">
          <Zap className="w-4 h-4 text-primary-foreground" />
        </div>
        <div>
          <p className="text-sm font-semibold leading-none text-foreground">DevFlow</p>
          <p className="text-[10px] text-muted-foreground mt-0.5">AI Platform</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto scrollbar-thin">
        {navItems.map(({ label, to, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
                isActive
                  ? 'bg-primary/10 text-primary font-medium'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent'
              )
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Backend status indicator */}
      <div className="px-4 py-2.5 border-t border-border">
        <div className="flex items-center gap-2">
          <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', statusDot[status])} />
          <span className="text-[10px] text-muted-foreground">
            Backend · {statusLabel[status]}
          </span>
        </div>
      </div>

      {/* Settings */}
      <div className="px-2 py-3 border-t border-border">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
              isActive
                ? 'bg-primary/10 text-primary font-medium'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent'
            )
          }
        >
          <Settings className="w-4 h-4 shrink-0" />
          Settings
        </NavLink>
      </div>
    </aside>
  )
}
