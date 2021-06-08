#!groovy

def workerNode = "devel10"

pipeline {

    agent {
        label workerNode
    }

    options {
        timestamps()
    }

    triggers {
        pollSCM('H/20 * * * *')
    }

    environment {
        DOCKER_IMAGE_VERSION = "${env.BRANCH_NAME}-${env.BUILD_NUMBER}"
    }

    stages {
        stage("Clean Workspace") {
            steps {
                deleteDir()
                checkout scm
            }
        }

        stage("docker build") {
            steps {
                script {
                    //docker build -t docker-io.dbc.dk/rawrepo-solr-indexer-scaler:master .
                    def image = docker.build("docker-io.dbc.dk/rawrepo-solr-indexer-scaler:${DOCKER_IMAGE_VERSION}")
                    image.push()
                }
            }
        }
    }

    post {
        always {
            cleanWs(deleteDirs: true)
        }
    }
}
