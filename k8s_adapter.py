#!/usr/bin/env python3
from kubernetes import client, config

NAMESPACE = "default"

def main():
    config.load_incluster_config()

    batch = client.BatchV1Api()

    job = client.V1Job(
        metadata=client.V1ObjectMeta(generate_name="ce-job-"),
        spec=client.V1JobSpec(
            backoff_limit=0,
            template=client.V1PodTemplateSpec(
                spec=client.V1PodSpec(
                    restart_policy="Never",
                    security_context=client.V1PodSecurityContext(
                        run_as_user=1100,
                        run_as_group=1100,
                        fs_group=1100,
                    ),
                    containers=[
                        client.V1Container(
                            name="payload",
                            image="alpine:3.20",
                            command=["/bin/sh", "-c"],
                            args=["echo hello from kubernetes"],
                            resources=client.V1ResourceRequirements(
                                requests={"cpu": "1", "memory": "128Mi"},
                                limits={"cpu": "1", "memory": "128Mi"},
                            ),
                        )
                    ],
                )
            ),
        ),
    )

    created = batch.create_namespaced_job(namespace=NAMESPACE, body=job)
    print(created.metadata.name)

if __name__ == "__main__":
    main()