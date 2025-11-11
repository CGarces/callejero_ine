## Ejecución Terraform

Inicialización terraform

```bash
terraform init
```

Selección de entorno

```bash
terraform workspace select ${TF_ENV} || terraform workspace new ${TF_ENV}
```

Ejecución plan

```bash
terraform plan -var-file=callejero-${TF_ENV}.tfvars -out tfapply
```

Ejecución apply
```bash
terraform apply tfapply
```
