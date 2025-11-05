# PAP Deployment Guide

**Version**: 1.0
**Status**: Draft
**Last Updated**: November 4, 2025

## 1. Overview

This guide provides reference deployment configurations for PAP using Kubernetes, Traefik ingress, and wildcard TLS certificates.

### 1.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DNS Layer                                │
│  a.plugged.in (delegated to cluster nameservers)           │
│  *.us-east.a.plugged.in → ingress-us-east.plugged.in       │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                   Traefik Ingress                            │
│  TLS termination, routing, rate limiting                    │
└───────────────────────────────┬─────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐     ┌────────▼────────┐    ┌────────▼────────┐
│ Research Agent │     │  Memory Agent   │    │   Focus Agent   │
│  (Pod)         │     │  (Pod)          │    │   (Pod)         │
└────────────────┘     └─────────────────┘    └─────────────────┘
```

---

## 2. Prerequisites

### 2.1 Infrastructure Requirements

- **Kubernetes**: v1.27+ (Rancher managed recommended)
- **Traefik**: v2.10+
- **Cert-Manager**: v1.13+ with DNS-01 challenge support
- **ExternalDNS**: v0.14+ with RFC2136 provider
- **DNS Server**: BIND9 or equivalent with RFC2136 dynamic updates

### 2.2 Required Secrets

```bash
# TLS certificate issuer credentials
kubectl create secret generic cloudflare-api-token \
  --from-literal=api-token=your-cloudflare-token

# Agent signing keys
kubectl create secret generic agent-signing-keys \
  --from-file=ed25519.key=./keys/agent-ed25519.key

# Station credentials
kubectl create secret generic station-credentials \
  --from-literal=station-id=plugged.in \
  --from-file=station-cert.pem=./certs/station.pem
```

---

## 3. DNS Configuration

### 3.1 DNS Delegation

Delegate `a.plugged.in` to cluster nameservers:

```bind
; In plugged.in zone
a.plugged.in.           IN    NS    ns1.plugged.in.
a.plugged.in.           IN    NS    ns2.plugged.in.

; Optional: DNSSEC delegation
a.plugged.in.           IN    DS    12345 13 2 (
                                    ABCD1234...
                                    )
```

### 3.2 Agent Zone Configuration

```bind
; In a.plugged.in zone (on ns1.plugged.in, ns2.plugged.in)
$ORIGIN a.plugged.in.
$TTL 300

@    IN    SOA    ns1.plugged.in. admin.plugged.in. (
              2025110401 ; Serial
              3600       ; Refresh
              900        ; Retry
              1209600    ; Expire
              300 )      ; Minimum TTL

@    IN    NS     ns1.plugged.in.
@    IN    NS     ns2.plugged.in.

; Wildcard records for regions
*.us-east    IN    CNAME    ingress-us-east.plugged.in.
*.eu-west    IN    CNAME    ingress-eu-west.plugged.in.
*.ap-south   IN    CNAME    ingress-ap-south.plugged.in.
```

### 3.3 ExternalDNS Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: external-dns-config
  namespace: kube-system
data:
  rfc2136.yaml: |
    ---
    server: "ns1.plugged.in"
    port: 53
    zone: "a.plugged.in"
    tsigKeyname: "externaldns-key"
    tsigSecret: "BASE64_ENCODED_SECRET=="
    tsigAlgorithm: "hmac-sha256"
```

---

## 4. Certificate Management

### 4.1 Cert-Manager ClusterIssuer

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-dns01
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@plugged.in
    privateKeySecretRef:
      name: letsencrypt-account-key
    solvers:
    - dns01:
        rfc2136:
          nameserver: "ns1.plugged.in:53"
          tsigKeyName: "cert-manager-key"
          tsigAlgorithm: HMACSHA256
          tsigSecretSecretRef:
            name: rfc2136-secret
            key: tsig-secret
```

### 4.2 Wildcard Certificate

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: wildcard-a-plugged-in
  namespace: agents
spec:
  secretName: wildcard-a-plugged-in-tls
  issuerRef:
    name: letsencrypt-dns01
    kind: ClusterIssuer
  dnsNames:
  - "*.us-east.a.plugged.in"
  - "*.eu-west.a.plugged.in"
  - "*.ap-south.a.plugged.in"
  duration: 2160h  # 90 days
  renewBefore: 720h  # 30 days
```

---

## 5. Agent Deployment

### 5.1 Agent Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: research-agent
  namespace: agents
  labels:
    app: research-agent
    agent-uuid: pluggedin/research@1.2.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: research-agent
  template:
    metadata:
      labels:
        app: research-agent
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: agent
        image: plugged.in/agents/research:v1.2.0
        env:
        - name: PAP_MODE
          value: "dual"  # Both PAP-CP and PAP-Hooks
        - name: PAP_CP_ENDPOINT
          value: "grpc://station.plugged.in:50051"
        - name: PAP_HOOKS_ENDPOINT
          value: "wss://gateway.plugged.in/hooks"
        - name: AGENT_UUID
          value: "pluggedin/research@1.2.0"
        - name: AGENT_REGION
          value: "us-east"
        - name: HEARTBEAT_MODE
          value: "IDLE"
        - name: HEARTBEAT_INTERVAL
          value: "30"
        volumeMounts:
        - name: tls-certs
          mountPath: /etc/pap/tls
          readOnly: true
        - name: signing-keys
          mountPath: /etc/pap/keys
          readOnly: true
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        - name: grpc
          containerPort: 50051
          protocol: TCP
        livenessProbe:
          exec:
            command:
            - /bin/pap-heartbeat
            - --check
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          periodSeconds: 10
          timeoutSeconds: 3
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
      volumes:
      - name: tls-certs
        secret:
          secretName: agent-tls-certs
      - name: signing-keys
        secret:
          secretName: agent-signing-keys
```

### 5.2 Agent Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: research-agent
  namespace: agents
  labels:
    app: research-agent
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 8080
    targetPort: 8080
    protocol: TCP
  - name: grpc
    port: 50051
    targetPort: 50051
    protocol: TCP
  selector:
    app: research-agent
```

---

## 6. Traefik Ingress

### 6.1 IngressRoute for PAP-Hooks

```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: research-agent-hooks
  namespace: agents
spec:
  entryPoints:
  - websecure
  routes:
  - match: Host(`research.us-east.a.plugged.in`) && PathPrefix(`/hooks`)
    kind: Rule
    services:
    - name: research-agent
      port: 8080
    middlewares:
    - name: rate-limit
    - name: auth-oauth
  tls:
    secretName: wildcard-a-plugged-in-tls
```

### 6.2 Middleware: Rate Limiting

```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: rate-limit
  namespace: agents
spec:
  rateLimit:
    average: 100
    burst: 200
    period: 1m
```

### 6.3 Middleware: OAuth Authentication

```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: auth-oauth
  namespace: agents
spec:
  forwardAuth:
    address: https://auth.plugged.in/verify
    authResponseHeaders:
    - X-Auth-User
    - X-Auth-Agent
    trustForwardHeader: true
```

---

## 7. Monitoring and Observability

### 7.1 Prometheus ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: research-agent
  namespace: agents
spec:
  selector:
    matchLabels:
      app: research-agent
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

### 7.2 Grafana Dashboard

```json
{
  "dashboard": {
    "title": "PAP Agent Metrics",
    "panels": [
      {
        "title": "Heartbeat Latency",
        "targets": [
          {
            "expr": "pap_cp_heartbeat_latency_seconds{agent=\"research\"}"
          }
        ]
      },
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(pap_hooks_requests_total{agent=\"research\"}[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(pap_hooks_errors_total{agent=\"research\"}[5m])"
          }
        ]
      }
    ]
  }
}
```

---

## 8. High Availability

### 8.1 Pod Disruption Budget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: research-agent-pdb
  namespace: agents
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: research-agent
```

### 8.2 Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: research-agent-hpa
  namespace: agents
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: research-agent
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 9. Security Hardening

### 9.1 NetworkPolicy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: research-agent-netpol
  namespace: agents
spec:
  podSelector:
    matchLabels:
      app: research-agent
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: traefik
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: station
    ports:
    - protocol: TCP
      port: 50051
  - to:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 53
```

### 9.2 PodSecurityPolicy

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: agent-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  volumes:
  - secret
  - configMap
  runAsUser:
    rule: MustRunAsNonRoot
  seLinux:
    rule: RunAsAny
  fsGroup:
    rule: RunAsAny
```

---

## 10. Backup and Disaster Recovery

### 10.1 Agent State Backup

```yaml
apiVersion: velero.io/v1
kind: Backup
metadata:
  name: agents-backup
  namespace: velero
spec:
  includedNamespaces:
  - agents
  includedResources:
  - deployments
  - services
  - secrets
  - configmaps
  storageLocation: default
  volumeSnapshotLocations:
  - default
  ttl: 720h  # 30 days
```

---

**Document Version**: 1.0
**Status**: Draft
**Last Updated**: November 4, 2025
