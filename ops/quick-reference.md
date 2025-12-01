# PAP Infrastructure - Quick Reference Guide

Quick commands for common operations on is.plugged.in infrastructure.

## DNS Operations

```bash
# Test DNS resolution
dig @185.96.168.242 is.plugged.in
dig @185.96.168.242 alice.is.plugged.in

# Reload BIND9 after zone changes
sudo rndc reload

# Check BIND9 status
sudo systemctl status named
sudo journalctl -u named -f

# Validate zone file before reload
sudo named-checkzone is.plugged.in /var/cache/bind/db.is.plugged.in
```

## Kubernetes Operations

```bash
# Cluster status
kubectl get nodes
kubectl get pods -A
kubectl top nodes  # Resource usage

# Agent namespace
kubectl get all -n agents
kubectl get pods -n agents
kubectl get ingress -n agents
kubectl get certificates -n agents
```

## Deploy New Agent

```bash
# Quick deploy (replace NAME)
export AGENT_NAME=alice
sed 's/{AGENT_NAME}/'$AGENT_NAME'/g; s/{AGENT_UUID}/prod\/'$AGENT_NAME'@v1.0/g' \
  /tmp/agent-deployment-template.yaml | kubectl apply -f -

# Check status
kubectl get pods -n agents -l agent-name=$AGENT_NAME
kubectl logs -n agents -l agent-name=$AGENT_NAME
```

## Certificate Management

```bash
# List all certificates
kubectl get certificate -A

# Check specific certificate
kubectl describe certificate {NAME} -n agents

# Force certificate renewal (delete to recreate)
kubectl delete certificate {NAME} -n agents

# Check ACME challenges
kubectl get challenge -A
kubectl describe challenge {NAME} -n agents

# cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager -f
```

## Traefik Operations

```bash
# Check Traefik service
kubectl get svc -n kube-system traefik

# View Traefik logs
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik -f

# Test ingress routing (from server)
curl -H "Host: is.plugged.in" http://localhost
curl -H "Host: alice.is.plugged.in" http://localhost
```

## Rancher Access

```bash
# Check Rancher container
docker ps | grep rancher
docker logs rancher -f

# Rancher URL
https://is.plugged.in

# Get Rancher bootstrap password (first login)
docker logs rancher 2>&1 | grep "Bootstrap Password:"
```

## Troubleshooting

```bash
# Pod not starting
kubectl describe pod {POD_NAME} -n agents
kubectl logs {POD_NAME} -n agents

# Certificate not issuing
kubectl get challenge -n agents
kubectl describe challenge {CHALLENGE_NAME} -n agents
kubectl logs -n agents -l acme.cert-manager.io/http01-solver=true

# DNS not resolving
dig @185.96.168.242 {DOMAIN} +trace
sudo journalctl -u named | tail -50

# Ingress not working
kubectl get ingress -n agents
kubectl describe ingress {NAME} -n agents
```

## Useful One-liners

```bash
# Watch pod status
watch kubectl get pods -n agents

# Get all agent endpoints
kubectl get ingress -n agents -o jsonpath='{range .items[*]}{.spec.rules[0].host}{"\n"}{end}'

# Check certificate expiry
kubectl get certificate -n agents -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.notAfter}{"\n"}{end}'

# Get all pods with resource usage
kubectl top pods -n agents

# Delete all failed pods
kubectl delete pods -n agents --field-selector status.phase=Failed

# Get events for troubleshooting
kubectl get events -n agents --sort-by='.lastTimestamp'
```

## Emergency Procedures

### BIND9 Not Responding
```bash
sudo systemctl restart named
sudo systemctl status named
dig @localhost is.plugged.in
```

### K3s Cluster Issues
```bash
sudo systemctl status k3s
sudo systemctl restart k3s
kubectl get nodes
```

### Certificate Expired
```bash
# Delete and recreate
kubectl delete certificate {NAME} -n {NAMESPACE}
# Will be recreated automatically by ingress annotation
```

### All Agents Down
```bash
# Check namespace
kubectl get all -n agents

# Check events
kubectl get events -n agents --sort-by='.lastTimestamp' | tail -20

# Check quotas
kubectl describe resourcequota -n agents
kubectl describe limitrange -n agents
```

## Monitoring Commands

```bash
# Resource usage summary
kubectl top nodes
kubectl top pods -n agents

# Certificate status overview
kubectl get certificates -A

# DNS query test
for subdomain in is alice bob charlie; do
  echo -n "$subdomain.is.plugged.in: "
  dig @185.96.168.242 $subdomain.is.plugged.in +short
done

# Ingress health check
kubectl get ingress -A
```

## Network Configuration

```bash
# View IP addresses
ip addr show ens18

# Test connectivity
ping -c 2 185.96.168.242
ping -c 2 185.96.168.243

# Check ports
sudo netstat -tlnp | grep -E ':(80|443|6443|53) '

# View netplan config
cat /etc/netplan/60-is-plugged-in.yaml
```

## Backup Commands

```bash
# Backup BIND9
sudo tar -czf /tmp/bind-backup-$(date +%Y%m%d).tar.gz /etc/bind /var/cache/bind

# Backup K8s resources
kubectl get all -A -o yaml > /tmp/k8s-all-$(date +%Y%m%d).yaml

# Backup agent namespace only
kubectl get all -n agents -o yaml > /tmp/k8s-agents-$(date +%Y%m%d).yaml

# Backup certificates (secrets)
kubectl get secrets -n agents -o yaml > /tmp/k8s-agent-secrets-$(date +%Y%m%d).yaml
```

## Environment Variables

```bash
# Set for kubectl commands
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Common namespace
export NAMESPACE=agents
```

## Logs Location

```bash
# BIND9
sudo journalctl -u named

# K3s
sudo journalctl -u k3s

# Docker (Rancher)
docker logs rancher

# Kubernetes pods
kubectl logs -n {NAMESPACE} {POD_NAME}
```

## Quick Health Check

```bash
#!/bin/bash
echo "=== Infrastructure Health Check ==="
echo ""
echo "DNS:"
dig @185.96.168.242 is.plugged.in +short
echo ""
echo "K3s:"
kubectl get nodes
echo ""
echo "Traefik:"
kubectl get svc -n kube-system traefik
echo ""
echo "cert-manager:"
kubectl get pods -n cert-manager
echo ""
echo "Agents:"
kubectl get pods -n agents
echo ""
echo "Certificates:"
kubectl get certificate -A
```
