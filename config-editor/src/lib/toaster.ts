import { createToaster } from '@skeletonlabs/skeleton-svelte';

export const toaster = createToaster({
  // @ts-expect-error - Skeleton Placement type mismatch with string literal
  placement: 'bottom-right',
  overlap: false
});
