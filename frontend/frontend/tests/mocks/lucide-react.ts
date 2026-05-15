import React from 'react'

// Mock all lucide-react icons as simple div components
const createMockIcon = (name: string) => {
  const MockIcon = React.forwardRef<
    SVGSVGElement,
    React.SVGProps<SVGSVGElement>
  >((props, ref) => (
    <svg ref={ref} data-testid={`icon-${name}`} {...props}>
      <title>{name}</title>
    </svg>
  ))
  MockIcon.displayName = name
  return MockIcon
}

export const Search = createMockIcon('Search')
export const X = createMockIcon('X')
export const ChevronDown = createMockIcon('ChevronDown')
export const ChevronRight = createMockIcon('ChevronRight')
export const ChevronLeft = createMockIcon('ChevronLeft')
export const ChevronUp = createMockIcon('ChevronUp')
export const ChevronsLeft = createMockIcon('ChevronsLeft')
export const ChevronsRight = createMockIcon('ChevronsRight')
export const Home = createMockIcon('Home')
export const Menu = createMockIcon('Menu')
export const Bell = createMockIcon('Bell')
export const Settings = createMockIcon('Settings')
export const User = createMockIcon('User')
export const LogOut = createMockIcon('LogOut')
export const CreditCard = createMockIcon('CreditCard')
export const Filter = createMockIcon('Filter')
export const ShoppingCart = createMockIcon('ShoppingCart')
export const Calendar = createMockIcon('Calendar')
export const ArrowRight = createMockIcon('ArrowRight')
export const ArrowLeft = createMockIcon('ArrowLeft')
export const Book = createMockIcon('Book')
export const Code = createMockIcon('Code')
export const Layers = createMockIcon('Layers')
export const Zap = createMockIcon('Zap')
export const Sun = createMockIcon('Sun')
export const Moon = createMockIcon('Moon')
export const Volume = createMockIcon('Volume')
export const Volume1 = createMockIcon('Volume1')
export const Volume2 = createMockIcon('Volume2')
export const VolumeX = createMockIcon('VolumeX')
export const ZoomIn = createMockIcon('ZoomIn')
export const ZoomOut = createMockIcon('ZoomOut')
export const Check = createMockIcon('Check')
export const Copy = createMockIcon('Copy')
export const Trash = createMockIcon('Trash')
export const Edit = createMockIcon('Edit')
export const Plus = createMockIcon('Plus')
export const Minus = createMockIcon('Minus')
export const Info = createMockIcon('Info')
export const AlertCircle = createMockIcon('AlertCircle')
export const AlertTriangle = createMockIcon('AlertTriangle')
export const CheckCircle = createMockIcon('CheckCircle')
export const XCircle = createMockIcon('XCircle')
export const Loader2 = createMockIcon('Loader2')
export const MoreHorizontal = createMockIcon('MoreHorizontal')
export const MoreVertical = createMockIcon('MoreVertical')
