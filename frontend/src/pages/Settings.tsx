import { Settings as SettingsIcon } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

export default function Settings() {
  return (
    <div className="space-y-6 max-w-xl">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Settings</h2>
        <p className="text-sm text-muted-foreground mt-0.5">
          Application configuration and preferences.
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <SettingsIcon className="w-4 h-4 text-muted-foreground" />
            <CardTitle>API Configuration</CardTitle>
          </div>
          <CardDescription>
            Configure the backend API endpoint for your DevFlow AI instance.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground" htmlFor="api-url">
              API Base URL
            </label>
            <Input
              id="api-url"
              placeholder="http://localhost:8000"
              defaultValue={import.meta.env.VITE_API_BASE_URL ?? ''}
            />
            <p className="text-xs text-muted-foreground">
              Set via <code className="text-xs font-mono bg-muted px-1 py-0.5 rounded">VITE_API_BASE_URL</code> environment variable.
            </p>
          </div>
          <Button size="sm" disabled>Save Changes</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>About</CardTitle>
          <CardDescription>DevFlow AI Frontend</CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Version</dt>
              <dd className="text-foreground font-mono text-xs">0.1.0</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Phase</dt>
              <dd className="text-foreground text-xs">Phase 1 — Foundation</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Backend</dt>
              <dd className="text-amber-500 text-xs">Not connected</dd>
            </div>
          </dl>
        </CardContent>
      </Card>
    </div>
  )
}
