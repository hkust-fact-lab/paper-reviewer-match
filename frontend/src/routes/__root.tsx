import { Outlet, createRootRoute } from '@tanstack/react-router'
import { Toaster } from '~/components/ui/toast'

export const Route = createRootRoute({
  component: () => (
    <>
      <Outlet />
      <Toaster />
    </>
  ),
})
