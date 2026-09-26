import { useState } from 'react'
import { Moon, Sun, Bell, Cpu, Globe, Info } from 'lucide-react'
import { Card, CardContent, CardHeader, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { useTheme } from '@/hooks/useTheme'
import { useBackendStatus } from '@/hooks/useBackendStatus'

function SectionHeading({ icon: Icon, title, description }: {
  icon: React.ComponentType<{ className?: string }>
  title: string
  description?: string
}) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <div className="flex items-center justify-center w-8 h-8 rounded-md bg-muted">
        <Icon className="w-4 h-4 text-muted-foreground" />
      </div>
      <div>
        <p className="text-sm font-semibold text-foreground">{title}</p>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>
    </div>
  )
}

export default function Settings() {
  const { theme, setTheme } = useTheme()
  const { status: backendStatus, recheck } = useBackendStatus()
  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_BASE_URL ?? '')

  return (
    <div className="space-y-5 max-w-2xl">
      {/* Appearance */}
      <Card>
        <CardHeader>
          <SectionHeading icon={Sun} title="Appearance" description="Theme and display preferences" />
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-xs font-medium text-foreground mb-2">Color theme</p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setTheme('dark')}
                className={`flex items-center gap-2 px-3 py-2 rounded-md border text-sm transition-colors ${theme === 'dark' ? 'border-primary/40 bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:text-foreground'}`}
              >
                <Moon className="w-3.5 h-3.5" />
                Dark
              </button>
              <button
                type="button"
                onClick={() => setTheme('light')}
                className={`flex items-center gap-2 px-3 py-2 rounded-md border text-sm transition-colors ${theme === 'light' ? 'border-primary/40 bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:text-foreground'}`}
              >
                <Sun className="w-3.5 h-3.5" />
                Light
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* API Configuration */}
      <Card>
        <CardHeader>
          <SectionHeading icon={Globe} title="API Configuration" description="Backend connection settings" />
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground" htmlFor="api-url">
              API Base URL
            </label>
            <div className="flex gap-2">
              <Input
                id="api-url"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="http://localhost:8000"
                className="flex-1"
              />
              <Button size="sm" variant="outline" disabled>Save</Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Set via <code className="text-xs font-mono bg-muted px-1 py-0.5 rounded">VITE_API_BASE_URL</code> environment variable.
            </p>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-foreground">Connection Status</p>
              <p className="text-xs text-muted-foreground mt-0.5">Backend API reachability</p>
            </div>
            <button
              type="button"
              onClick={recheck}
              className={`flex items-center gap-1.5 text-xs cursor-pointer hover:opacity-80 transition-opacity ${
                backendStatus === 'online'
                  ? 'text-success'
                  : backendStatus === 'offline'
                  ? 'text-error'
                  : 'text-amber-500'
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${
                backendStatus === 'online'
                  ? 'bg-success'
                  : backendStatus === 'offline'
                  ? 'bg-error'
                  : 'bg-amber-500 animate-pulse'
              }`} />
              {backendStatus === 'online' ? 'Connected' : backendStatus === 'offline' ? 'Unreachable' : 'Checking…'}
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Workflow Preferences */}
      <Card>
        <CardHeader>
          <SectionHeading icon={Cpu} title="Workflow Preferences" description="Default settings for workflow runs" />
        </CardHeader>
        <CardContent>
          <div className="p-3 rounded-md bg-muted/50 border border-border">
            <p className="text-xs text-muted-foreground">
              Workflow configuration options such as agent timeouts and approval thresholds will be available in a future release.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <SectionHeading icon={Bell} title="Notifications" description="Alert and notification preferences" />
        </CardHeader>
        <CardContent>
          <div className="p-3 rounded-md bg-muted/50 border border-border">
            <p className="text-xs text-muted-foreground">
              Email and webhook notifications will be available in a future release.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* About */}
      <Card>
        <CardHeader>
          <SectionHeading icon={Info} title="About" />
          <CardDescription>DevFlow AI Platform</CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="space-y-2">
            <MetaRow label="Version" value="0.1.0" />
            <MetaRow label="Phase" value="Phase 7 — Frontend Integration & Production Polish" />
            <MetaRow label="Stack" value="React 19 · TypeScript 6 · Tailwind v4 · Vite 8" />
            <MetaRow label="Backend" value="Connected — FastAPI 0.141 · in-memory store" />
          </dl>
        </CardContent>
      </Card>
    </div>
  )
}

function MetaRow({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-border last:border-b-0">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className={`text-xs font-medium ${warn ? 'text-amber-500' : 'text-foreground'}`}>{value}</dd>
    </div>
  )
}
