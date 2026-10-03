pipeline {
    agent any

    stages {

        stage('Build Docker Image') {
            steps {
                bat '"C:\\Users\\aravi\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" build -t smart-parking:test .'
            }
        }

        stage('Run Tests') {
            steps {
                bat '"C:\\Users\\aravi\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" run --rm smart-parking:test python -m pytest -v'
            }
        }
    }

    post {
        success {
            echo 'Smart Parking CI/CD Pipeline completed successfully!'
        }

        failure {
            echo 'Pipeline failed. Check the stage logs.'
        }
    }
}