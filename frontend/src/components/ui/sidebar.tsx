import * as React from "react"
import { PanelLeft } from "lucide-react"
import { cn } from "@/lib/utils"

interface SidebarContextValue {
  open: boolean
  setOpen: (open: boolean) => void
  openMobile: boolean
  setOpenMobile: (open: boolean) => void
  isMobile: boolean
  toggleSidebar: () => void
  state: "expanded" | "collapsed"
}

const SidebarContext = React.createContext<SidebarContextValue | null>(null)

export function useSidebar() {
  const context = React.useContext(SidebarContext)
  if (!context) {
    return {
      open: true,
      setOpen: () => {},
      openMobile: false,
      setOpenMobile: () => {},
      isMobile: false,
      toggleSidebar: () => {},
      state: "expanded" as const,
    }
  }
  return context
}

export function SidebarProvider({
  defaultOpen = true,
  open: openProp,
  onOpenChange: setOpenProp,
  className,
  style,
  children,
  ...props
}: {
  defaultOpen?: boolean
  open?: boolean
  onOpenChange?: (open: boolean) => void
  className?: string
  style?: React.CSSProperties
  children: React.ReactNode
}) {
  const [openState, setOpenState] = React.useState(defaultOpen)
  const [openMobile, setOpenMobile] = React.useState(false)
  const [isMobile, setIsMobile] = React.useState(false)

  React.useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024)
    }
    checkMobile()
    window.addEventListener("resize", checkMobile)
    return () => window.removeEventListener("resize", checkMobile)
  }, [])

  const open = openProp ?? openState
  const setOpen = React.useCallback(
    (value: boolean | ((value: boolean) => boolean)) => {
      const openState = typeof value === "function" ? value(open) : value
      if (setOpenProp) {
        setOpenProp(openState)
      } else {
        setOpenState(openState)
      }
    },
    [setOpenProp, open]
  )

  const toggleSidebar = React.useCallback(() => {
    if (isMobile) {
      setOpenMobile((prev) => !prev)
    } else {
      setOpen((prev) => !prev)
    }
  }, [isMobile, setOpen])

  const state = open ? "expanded" : "collapsed"

  return (
    <SidebarContext.Provider
      value={{
        open,
        setOpen,
        openMobile,
        setOpenMobile,
        isMobile,
        toggleSidebar,
        state,
      }}
    >
      <div
        style={style}
        data-state={state}
        className={cn("flex min-h-screen w-full", className)}
        {...props}
      >
        {children}
      </div>
    </SidebarContext.Provider>
  )
}

export const Sidebar = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    collapsible?: "offcanvas" | "icon" | "none"
  }
>(({ className, collapsible = "icon", children, ...props }, ref) => {
  const { open, isMobile, openMobile, setOpenMobile } = useSidebar()

  return (
    <>
      {/* Mobile Drawer Backdrop */}
      {isMobile && openMobile && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setOpenMobile(false)}
        />
      )}
      <aside
        ref={ref}
        data-collapsible={!open ? collapsible : undefined}
        data-state={open ? "expanded" : "collapsed"}
        className={cn(
          "group flex flex-col shrink-0 border-r border-sidebar-border bg-sidebar transition-all duration-300 ease-in-out",
          // Desktop sizing
          open ? "w-[var(--sidebar-width,18.125rem)]" : "w-[var(--sidebar-width-icon,4.25rem)]",
          // Mobile drawer
          isMobile && (openMobile ? "fixed inset-y-0 left-0 z-50 w-[18.125rem] shadow-2xl flex" : "hidden"),
          className
        )}
        {...props}
      >
        {children}
      </aside>
    </>
  )
})
Sidebar.displayName = "Sidebar"

export function SidebarHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col p-4 shrink-0", className)} {...props} />
}

export function SidebarContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-1 flex-col overflow-y-auto px-3 py-2 no-scrollbar", className)} {...props} />
}

export function SidebarFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col p-3 shrink-0", className)} {...props} />
}

export function SidebarGroup({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col py-2", className)} {...props} />
}

export function SidebarGroupLabel({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "px-3 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider group-data-[collapsible=icon]:hidden",
        className
      )}
      {...props}
    />
  )
}

export function SidebarGroupContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("w-full", className)} {...props} />
}

export function SidebarMenu({ className, ...props }: React.HTMLAttributes<HTMLUListElement>) {
  return <ul className={cn("flex flex-col gap-1 list-none p-0 m-0", className)} {...props} />
}

export function SidebarMenuItem({ className, ...props }: React.HTMLAttributes<HTMLLIElement>) {
  return <li className={cn("relative list-none", className)} {...props} />
}

export interface SidebarMenuButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
  isActive?: boolean
  tooltip?: string
}

export const SidebarMenuButton = React.forwardRef<HTMLButtonElement, SidebarMenuButtonProps>(
  ({ className, asChild = false, isActive = false, tooltip, children, ...props }, ref) => {
    // If asChild and children is a single React element, clone with classes
    if (asChild && React.isValidElement(children)) {
      const child = children as React.ReactElement<{ className?: string; 'aria-current'?: string }>
      return React.cloneElement(child, {
        className: cn(
          "flex items-center w-full gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-colors cursor-pointer",
          isActive && "bg-sidebar-accent text-sidebar-accent-foreground font-semibold",
          child.props.className,
          className
        ),
        'aria-current': isActive ? 'page' : undefined,
      })
    }

    return (
      <button
        ref={ref}
        aria-current={isActive ? "page" : undefined}
        className={cn(
          "flex items-center w-full gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-colors cursor-pointer",
          isActive && "bg-sidebar-accent text-sidebar-accent-foreground font-semibold",
          className
        )}
        {...props}
      >
        {children}
      </button>
    )
  }
)
SidebarMenuButton.displayName = "SidebarMenuButton"

export function SidebarMenuBadge({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "ml-auto text-[11px] font-bold px-2 py-0.5 rounded-full group-data-[collapsible=icon]:hidden",
        className
      )}
      {...props}
    />
  )
}

export function SidebarTrigger({ className, onClick, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { toggleSidebar } = useSidebar()
  return (
    <button
      onClick={(e) => {
        toggleSidebar()
        onClick?.(e)
      }}
      className={cn(
        "inline-flex items-center justify-center rounded-lg p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer",
        className
      )}
      {...props}
    >
      <PanelLeft className="size-5" />
      <span className="sr-only">Toggle Sidebar</span>
    </button>
  )
}
