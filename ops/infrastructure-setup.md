# PAP Infrastructure Setup Documentation

**Date**: 2026-11-13
**Server**: is.plugged.in (185.96.168.254)
**Status**: Production Ready

## Overview

Complete infrastructure setup for PAP (Plugged.in Agent Protocol) v1.0 on is.plugged.in, including:
- DNS infrastructure with BIND9 nameservers
- Kubernetes cluster (K3s) with Traefik ingress
- Certificate management with Let's Encrypt
- Agent deployment infrastructure

---

## 1. Network Configuration

### IP Addresses
- **185.96.168.254**: Main server (is.plugged.in, Traefik LoadBalancer)
- **185.96.168.242**: ns1.is.plugged.in (Primary DNS server)
- **185.96.168.243**: ns2.is.plugged.in (Secondary DNS server)

### Network Interface
All IPs configured on `ens18`:
```bash
ip addr show ens18
```

Configuration file: `/etc/netplan/60-is-plugged-in.yaml`
```yaml
network:
  version: 2
  ethernets:
    ens18:
      addresses:
        - 185.96.168.242/28
        - 185.96.168.243/28
```

---

## 2. DNS Infrastructure (BIND9)

### Installation
```bash
sudo apt-get install bind9 bind9utils bind9-doc dnsutils
```

### Configuration Files

**Zone File**: `/var/cache/bind/db.is.plugged.in`
- Serial: 2026111301
- SOA: ns1.is.plugged.in
- Wildcard DNS: `*.is.plugged.in` → 185.96.168.254

**BIND9 Config**: `/etc/bind/named.conf.local`
- TSIG Key: `/etc/bind/keys/cert-manager.key`
- Allows RFC2136 dynamic updates for cert-manager

**Listen Addresses**: `/etc/bind/named.conf.options`
- 127.0.0.1
- 185.96.168.254
- 185.96.168.242
- 185.96.168.243

### Testing DNS
```bash
dig @185.96.168.242 is.plugged.in
dig @185.96.168.242 test.is.plugged.in  # Tests wildcard
```

---

## 3. Kubernetes Cluster (K3s)

### Installation
```bash
curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
```

**Version**: v1.33.5+k3s1
**Kubeconfig**: `/etc/rancher/k3s/k3s.yaml`

### Cluster Status
```bash
kubectl get nodes
kubectl get pods -A
```

### Pre-installed Components
- **Traefik** v2.x (Ingress controller)
- **CoreDNS** (Cluster DNS)
- **metrics-server** (Resource metrics)
- **local-path-provisioner** (Storage)

---

## 4. Traefik Ingress Controller

### Service
```bash
kubectl get svc -n kube-system traefik
```

**Type**: LoadBalancer
**External-IP**: 185.96.168.254
**Ports**: 80 (HTTP), 443 (HTTPS)

### Features
- TLS termination with Let's Encrypt certificates
- SNI-based routing for multiple domains
- Rate limiting middleware
- HTTP → HTTPS redirects

---

## 5. Certificate Management (cert-manager)

### Installation
```bash
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --version v1.16.2 --set crds.enabled=true
```

### ClusterIssuers

**HTTP-01 (Production)**:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@plugged.in
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: traefik
```

**DNS-01 (For Wildcard Certificates)**:
- ClusterIssuer: `letsencrypt-dns01-prod`
- Configured with RFC2136
- TSIG Secret: `rfc2136-secret` in cert-manager namespace
- Status: Configuration ready, requires zone autodiscovery fix for production use

### Successful Certificates
- ✅ is.plugged.in (Rancher UI) - **VERIFIED WORKING**

---

## 6. Rancher UI

### Container
```bash
docker ps | grep rancher
```

**Image**: rancher/rancher:latest
**Ports**: 8080 (HTTP), 8443 (HTTPS)
**Access**: Behind Traefik at https://is.plugged.in

### Kubernetes Integration
- Rancher Docker container runs on host
- K3s cluster managed separately
- Can be integrated via Rancher UI

---

## 7. Agent Infrastructure

### Namespace
```bash
kubectl get namespace agents
```

**Pod Security**: Restricted (enforced)
**Features**:
- RBAC (ServiceAccount: `pap-agent`)
- NetworkPolicy (pod isolation)
- ResourceQuota (40 CPU, 200Gi memory, 100 pods max)
- LimitRange (100m-2 CPU, 256Mi-4Gi memory per container)

### Deployment Template
Location: `/tmp/agent-deployment-template.yaml`

**Template Variables**:
- `{AGENT_NAME}`: Agent subdomain (e.g., alice, bob)
- `{AGENT_UUID}`: PAP agent UUID (e.g., namespace/agent@v1.0)

**Components**:
1. Deployment (1 replica, non-root security context)
2. Service (ClusterIP)
3. Ingress (with Let's Encrypt cert annotation)

### Security Features
- **runAsNonRoot**: true
- **runAsUser**: 1001
- **fsGroup**: 1001
- **allowPrivilegeEscalation**: false
- **capabilities drop**: ALL
- **seccompProfile**: RuntimeDefault

---

## 8. Firewall Configuration

### Main Server (185.96.168.254)
```
Inbound:
  22/tcp   - SSH
  80/tcp   - HTTP (Let's Encrypt, redirects)
  443/tcp  - HTTPS (Rancher UI + all agents)
  6443/tcp - Kubernetes API (optional)

Outbound:
  53/tcp+udp - DNS queries
  80/tcp     - HTTP (updates, registries)
  443/tcp    - HTTPS (Let's Encrypt, registries)
```

### Nameservers (185.96.168.242, 185.96.168.243)
```
Inbound:
  22/tcp      - SSH
  53/tcp+udp  - DNS queries (public)
  53/tcp+udp  - RFC2136 updates (from 185.96.168.254 only)

Outbound:
  53/tcp+udp - DNS queries to upstream servers
```

---

## 9. Deployment Procedures

### Deploy New Agent

1. **Copy template**:
   ```bash
   cp /tmp/agent-deployment-template.yaml agent-{NAME}.yaml
   ```

2. **Substitute variables**:
   ```bash
   sed -i 's/{AGENT_NAME}/alice/g' agent-alice.yaml
   sed -i 's/{AGENT_UUID}/prod\/alice@v1.0/g' agent-alice.yaml
   ```

3. **Update image** (when PAP agent container is ready):
   Replace `image: nginx:alpine` with actual PAP agent image

4. **Deploy**:
   ```bash
   kubectl apply -f agent-alice.yaml
   ```

5. **Verify**:
   ```bash
   kubectl get pods -n agents
   kubectl get ingress -n agents
   kubectl get certificate -n agents
   ```

6. **Test DNS**:
   ```bash
   dig alice.is.plugged.in
   ```

7. **Test HTTPS** (once cert is issued):
   ```bash
   curl https://alice.is.plugged.in
   ```

---

## 10. Monitoring and Troubleshooting

### Check DNS
```bash
# Test local DNS
dig @185.96.168.242 is.plugged.in

# Test wildcard
dig @185.96.168.242 test.is.plugged.in

# Check BIND9 logs
sudo journalctl -u named -f
```

### Check Kubernetes
```bash
# Cluster health
kubectl get nodes
kubectl get pods -A

# cert-manager status
kubectl get clusterissuers
kubectl get certificates -A
kubectl logs -n cert-manager -l app=cert-manager

# Traefik status
kubectl get svc -n kube-system traefik
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik
```

### Check Certificates
```bash
# List all certificates
kubectl get certificate -A

# Describe certificate (for errors)
kubectl describe certificate {NAME} -n {NAMESPACE}

# Check ACME challenges
kubectl get challenge -A
```

### Common Issues

**Certificate pending**:
```bash
# Check challenge status
kubectl get challenge -n agents
kubectl describe challenge {NAME} -n agents

# Check solver pods
kubectl get pods -n agents | grep solver
kubectl logs -n agents {SOLVER_POD}
```

**DNS not resolving**:
```bash
# Restart BIND9
sudo systemctl restart named

# Check configuration
sudo named-checkconf
sudo named-checkzone is.plugged.in /var/cache/bind/db.is.plugged.in
```

**Pod crashes**:
```bash
# Check logs
kubectl logs -n agents {POD_NAME}

# Check events
kubectl describe pod -n agents {POD_NAME}

# Check security context
kubectl get pod -n agents {POD_NAME} -o yaml | grep -A 10 securityContext
```

---

## 11. Maintenance

### Update DNS Zone
1. Edit: `/var/cache/bind/db.is.plugged.in`
2. Increment serial number (format: YYYYMMDDNN)
3. Reload BIND9: `sudo rndc reload`
4. Verify: `dig @185.96.168.242 {RECORD}`

### Rotate Certificates
Automatic via cert-manager (90 days before expiry)

Manual renewal (if needed):
```bash
kubectl delete certificate {NAME} -n {NAMESPACE}
# Certificate will be automatically recreated
```

### Update K3s
```bash
curl -sfL https://get.k3s.io | sh -
sudo systemctl restart k3s
```

### Backup Critical Data
```bash
# BIND9 zone files
sudo tar -czf bind-backup-$(date +%Y%m%d).tar.gz /etc/bind /var/cache/bind

# Kubernetes resources
kubectl get all -A -o yaml > k8s-resources-$(date +%Y%m%d).yaml

# Certificates (secrets)
kubectl get secrets -A -o yaml > k8s-secrets-$(date +%Y%m%d).yaml
```

---

## 12. Architecture Summary

```
Internet
   │
   ├─> ns1.is.plugged.in:53 (185.96.168.242)     [BIND9 Primary DNS]
   ├─> ns2.is.plugged.in:53 (185.96.168.243)     [BIND9 Secondary DNS]
   │
   └─> is.plugged.in:443 (185.96.168.254)        [Traefik LoadBalancer]
         │
         ├─> is.plugged.in                        [Rancher UI] ✅ Let's Encrypt Cert
         ├─> alice.is.plugged.in                  [Agent Pod]
         ├─> bob.is.plugged.in                    [Agent Pod]
         └─> *.is.plugged.in                      [Any Agent Pod]
               │
               └─> agents namespace
                     ├─> Deployment (non-root, secured)
                     ├─> Service (ClusterIP)
                     ├─> Ingress (Let's Encrypt cert)
                     └─> NetworkPolicy (isolated)
```

---

## 13. Next Steps

### Immediate
- [ ] Build PAP agent container image (from PAP-Implementation.md specs)
- [ ] Deploy first production agent
- [ ] Integrate Rancher with K3s cluster (optional)

### Future Enhancements
- [ ] Fix DNS-01 wildcard certificate autodiscovery
- [ ] Deploy ExternalDNS for automatic DNS record management
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Implement agent hibernation/scaling
- [ ] Multi-region deployment support

---

## 14. References

- **PAP Specification**: `/home/pluggedin/PAP/PAP/docs/rfc/pap-rfc-001-v1.0.md`
- **Implementation Plan**: `/home/pluggedin/PAP/PAP-Implementation.md`
- **K3s Documentation**: https://docs.k3s.io
- **cert-manager Documentation**: https://cert-manager.io
- **Traefik Documentation**: https://doc.traefik.io/traefik/

---

## 15. Success Criteria

✅ **All Completed**:
1. Network interfaces configured (3 IPs)
2. BIND9 DNS servers operational
3. Wildcard DNS functioning (`*.is.plugged.in`)
4. K3s cluster healthy and running
5. Traefik ingress operational
6. cert-manager installed and functional
7. Let's Encrypt production certificates working (is.plugged.in verified)
8. Rancher UI accessible via HTTPS with valid certificate
9. Agent namespace created with security policies
10. Deployment templates ready
11. Infrastructure fully documented

**Infrastructure Status**: **PRODUCTION READY** 🚀

Agent deployment can proceed once PAP agent container images are built.
