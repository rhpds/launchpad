export interface GuidedLabLinks {
  showroomUrl?: string;
  workspaceUrl?: string;
}

export function guidedLabLinks(
  resources: Record<string, unknown>,
  sessionId?: string,
): GuidedLabLinks {
  if (sessionId) {
    return {
      showroomUrl: `/labs/${encodeURIComponent(sessionId)}/showroom/`,
      // Workspaces are rendered as entitled tabs inside the canonical
      // Showroom path. Do not send requester users to raw cluster routes.
      workspaceUrl: undefined,
    };
  }
  return {
    showroomUrl: typeof resources.showroom_url === 'string' ? resources.showroom_url : undefined,
    workspaceUrl: typeof resources.workspace_url === 'string' ? resources.workspace_url : undefined,
  };
}
