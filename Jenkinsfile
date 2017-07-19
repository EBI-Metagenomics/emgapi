node {
    configure()
}

private void configure() {
    stage("configure") {
        checkout scm
        sh '/nfs/public/rw/xfam/python3/bin/python3 -V'
        sh 'SRCDIR=$(pwd)/src VENVDIR=$(pwd)/venv PYTHONENV=/nfs/public/rw/xfam/python3/bin/python3 src/docker/run.sh jenkins'
    }
}