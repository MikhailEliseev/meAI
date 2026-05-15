import { vi } from 'vitest'

// Mock cmdk components
export const Command = ({ children, className, ...props }: any) => (
  <div data-testid="command" className={className} {...props}>
    {children}
  </div>
)

export const CommandDialog = ({ children, open, onOpenChange, ...props }: any) => (
  open ? (
    <div data-testid="command-dialog" {...props}>
      {children}
    </div>
  ) : null
)

export const CommandInput = ({ value, onValueChange, onKeyDown, placeholder, ...props }: any) => (
  <input
    data-testid="command-input"
    placeholder={placeholder}
    value={value}
    onChange={(e) => onValueChange?.(e.target.value)}
    onKeyDown={onKeyDown}
    {...props}
  />
)

export const CommandList = ({ children, ...props }: any) => (
  <div data-testid="command-list" {...props}>
    {children}
  </div>
)

export const CommandEmpty = ({ children, ...props }: any) => (
  <div data-testid="command-empty" {...props}>
    {children}
  </div>
)

export const CommandGroup = ({ children, heading, ...props }: any) => (
  <div data-testid="command-group" {...props}>
    {heading && <div data-testid="command-group-heading">{heading}</div>}
    {children}
  </div>
)

export const CommandItem = ({ children, onSelect, value, ...props }: any) => (
  <div
    data-testid="command-item"
    data-value={value}
    onClick={() => onSelect?.(value)}
    {...props}
  >
    {children}
  </div>
)

export const CommandSeparator = (props: any) => (
  <div data-testid="command-separator" {...props} />
)

export const CommandShortcut = ({ children, ...props }: any) => (
  <span data-testid="command-shortcut" {...props}>
    {children}
  </span>
)
