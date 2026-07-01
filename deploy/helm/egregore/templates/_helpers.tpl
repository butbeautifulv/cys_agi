{{- define "egregore.fullname" -}}
{{- printf "%s" .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "egregore.labels" -}}
app.kubernetes.io/name: egregore
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
