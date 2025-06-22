# Setting up the postgres k8s 

I'll assume you set this one up before setting up the main application

```
microk8s kubectl create namespace stocks
microk8s helm3 install stocks oci://registry-1.docker.io/bitnamicharts/postgresql --namespace stocks
```
Run the command displayed on your screen to get the password. 

Now we just need to be able to reach it from outside the cluster too, since we cant really test on my local machine otherwise.

```
microk8s kubectl config set-context --current --namespace=stocks
microk8s kubectl edit service stocks-postgresql
```

![img.png](img.png)

Change the values in the config.cfg like this:
``` 
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:<YOUR PASSWORD HERE>@<YOUR HOST IP HERE>:<YOUR NODEPORT PORT HERE>/'
```