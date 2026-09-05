{{- define "agentops.runtimeSecret" -}}
{{- required "runtime.existingSecret is required" .Values.runtime.existingSecret -}}
{{- end -}}

{{- define "agentops.selectorLabels" -}}
app.kubernetes.io/name: agentops-seat
app.kubernetes.io/instance: {{ .Release.Name | quote }}
{{- end -}}

{{- define "agentops.labels" -}}
{{ include "agentops.selectorLabels" . }}
app.kubernetes.io/managed-by: launchpad
app.kubernetes.io/part-of: agentops-observability
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | quote }}
launchpad.redhat.com/session-id: {{ required "identity.sessionId is required" .Values.identity.sessionId | quote }}
launchpad.redhat.com/workshop-id: {{ required "identity.workshopId is required" .Values.identity.workshopId | quote }}
launchpad.redhat.com/seat-id: {{ required "identity.seatId is required" .Values.identity.seatId | quote }}
launchpad.redhat.com/tenant: {{ required "identity.tenantId is required" .Values.identity.tenantId | quote }}
launchpad.redhat.com/cluster-id: {{ required "identity.clusterId is required" .Values.identity.clusterId | quote }}
{{- end -}}

{{- define "agentops.podSecurityContext" -}}
runAsNonRoot: true
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{- define "agentops.containerSecurityContext" -}}
allowPrivilegeEscalation: false
capabilities:
  drop: ["ALL"]
runAsNonRoot: true
{{- end -}}
