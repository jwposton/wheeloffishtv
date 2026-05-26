import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface ThemeToggleProps {
  compact?: boolean
  className?: string
}

export function ThemeToggle({ compact = false, className }: ThemeToggleProps) {
  const { setTheme, resolvedTheme } = useTheme()

  const isDark = resolvedTheme === "dark"

  return (
    <Button
      type="button"
      variant="outline"
      size={compact ? "icon-sm" : "icon"}
      className={cn("relative", className)}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      <Sun
        className={cn(
          "scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90",
          compact ? "size-3.5" : "size-4",
        )}
      />
      <Moon
        className={cn(
          "absolute scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0",
          compact ? "size-3.5" : "size-4",
        )}
      />
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}
