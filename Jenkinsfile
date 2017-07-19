node {
    configure()
}

private void configure() {
    stage("configure") {
        checkout scm
        sh 'virtualenv -p /nfs/public/rw/xfam/python3/bin/python3 emg_venv'
    }
}