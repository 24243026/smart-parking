pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t smart-parking:test .'
            }
        }

        stage('Run Tests') {
            steps {
                bat 'docker run --rm smart-parking:test python -m pytest -v'
            }
        }
    }

    post {
        success {
            echo 'Smart Parking CI Pipeline completed successfully!'
        }

        failure {
            echo 'Pipeline failed. Check the stage logs.'
        }
    }
}