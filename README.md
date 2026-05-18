# Local installation procedure on minikube

## Create the required docker image
docker build -f Dockerfile.htcondor-ce-k8s -t cpel/htcondor-ce-k8s:latest .
docker push cpel/htcondor-ce-k8s:latest

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