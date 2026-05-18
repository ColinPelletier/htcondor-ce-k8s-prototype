# HTCondor-CE to Kubernetes Jobs Prototype

This prototype evaluates whether jobs submitted through an HTCondor-CE environment can be executed as Kubernetes Jobs.

The main goal is feasibility testing: verify that the CE pod can interact with the Kubernetes API, identify what works, and document the missing components required for full `condor_submit` integration.

## Current Status

### Implemented

- HTCondor-CE container without Slurm dependencies
- Kubernetes Deployment, Service, PVCs, ServiceAccount, and RBAC to create Kubernetes Jobs
- Python adapter: `k8s_adapter.py`

Validated flow:

```text
CE pod → k8s_adapter.py → Kubernetes Job → Pod runs
```

This confirms that the CE pod can successfully create Kubernetes Jobs.

## Current Limitation

Direct `condor_submit` does not launch Kubernetes Jobs yet.

Current behavior:

```text
condor_submit → HTCondor-CE queue → job stays idle
```

Reason: HTCondor-CE is not an execution node.

In the previous setup, Slurm provided the execution backend:

```text
HTCondor-CE → BLAHP → Slurm workers
```

For Kubernetes, this backend bridge does not exist yet.

## Missing Component
A bridge is needed between the HTCondor-CE queue and Kubernetes.

Required flow:

```text
HTCondor-CE queue → adapter / watcher → Kubernetes Job
```

The bridge should:
- Watch the HTCondor-CE queue
- Detect new jobs
- Create matching Kubernetes Jobs

Future work should also include:
- Status synchronization
- Job cancellation
- Logs and output handling
- Resource mapping


# Local installation procedure on minikube

## Create the required docker image
```bash
docker build -f Dockerfile.htcondor-ce-k8s -t cpel/htcondor-ce-k8s:latest .  
docker push cpel/htcondor-ce-k8s:latest
```

## Apply changes
```bash
kubectl apply -f service-account.yaml
kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```


### Testing that the infra is working properly (step-by-step)
Run a test job to make sure the k8s part is working properly:
```bash
kubectl create -f job-template.yaml
```

See that the job is running and that is produces the correct output
```bash
kubectl get jobs
kubectl logs <job-pod-name>
```

If this works, the template Kubernetes side should be working correctly. We can then try to run the same job from our Python adapter script inside htcondor-ce.

```bash
kubectl exec -it htcondor-ce-<pod-id> -- python3 /usr/local/bin/k8s_adapter.py
```

Verify the job pod is there and the job output
```bash
kubectl get jobs
kubectl get pods
kubectl logs <new-job-pod>
```

If this works, it verifies that our adapter can send K8s jobs.

## Next step: run the job from HTCondor-CE system
--> Experimental, doesn't work yet. The next step would consist of creating a BLAHP wrapper or something similar.

Inside the CE pod, run:
```bash
export CONDOR_CONFIG=/etc/condor-ce/condor_config
```

```bash
kubectl exec -i htcondor-ce-<pod-id> -- bash -c '
cat > /tmp/hello-k8s.sub <<EOF
universe = vanilla
executable = /usr/local/bin/k8s_adapter.py
log = /tmp/hello-k8s.log
output = /tmp/hello-k8s.out
error = /tmp/hello-k8s.err
queue
EOF

SCHEDD_ADDR=$(cat /var/lib/condor-ce/spool/.schedd_address | head -1)

runuser -u testce -- env CONDOR_CONFIG=/etc/condor-ce/condor_config \
  condor_submit -addr "$SCHEDD_ADDR" /tmp/hello-k8s.sub
'
```

## Conclusion

This prototype confirms that Kubernetes Job creation from inside the HTCondor-CE pod is feasible.

However, full `condor_submit` support requires an additional backend bridge that plays the role previously handled by BLAHP and Slurm. This bridge must watch the HTCondor-CE queue, create Kubernetes Jobs, and eventually synchronize job status, cancellation, logs, outputs, and resource requirements.