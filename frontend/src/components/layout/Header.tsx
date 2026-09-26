import { useLocation } from 'react-router-dom'
import { Bell, Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useTheme } from '@/hooks/useTheme'

const pageTitles: Record<string, { title: string; description: string }> = {
  '/': { title: 'Dashboard', description: 'Overview of your workflow activity' },
  '/repositories': { title: 'Repositories', description: 'Manage connected repositories' },
  '/workflow': { title: 'Workflow', description: 'AI agent pipeline status' },
  '/findings': { title: 'Findings', description: 'Issues discovered by AI agents' },
  '/reports': { title: 'Reports', description: 'Workflow analysis reports' },
  '/settings': { title: 'Settings', description: 'Application configuration' },
}

export function Header() {
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()
  const page = pageTitles[location.pathname] ?? { title: 'DevFlow AI', description: '' }

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-border bg-card shrink-0">
      <div>
        <h1 className="text-sm font-semibold text-foreground">{page.title}</h1>
        <p className="text-xs text-muted-foreground">{page.description}</p>
      </div>

      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          aria-label="Notifications"
          className="text-muted-foreground"
        >
          <Bell className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Toggle theme"
          className="text-muted-foreground"
          onClick={toggleTheme}
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </Button>
      </div>
    </header>
  )
}
