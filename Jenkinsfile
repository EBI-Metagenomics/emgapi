node {
    configure()
}

private void configure() {
    stage("configure") {
        checkout scm
        sh '/nfs/public/rw/xfam/python3/bin/python3 -V'
        sh 'HOMEDIR=$(pwd) PYTHONENV=/nfs/public/rw/xfam/python3/bin/python3 src/docker/run.sh jenkins'
    }
}