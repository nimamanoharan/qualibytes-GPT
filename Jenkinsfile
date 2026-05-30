pipeline {
    agent any

    environment {
        DOCKER_IMAGE_FRONTEND = "${DOCKER_USERNAME}/qualibytes-frontend"
        DOCKER_IMAGE_BACKEND  = "${DOCKER_USERNAME}/qualibytes-backend"
        APP_SERVER_IP         = "172.31.25.2"
        DOCKER_CREDS          = credentials('dockerhub-credentials')
    }

    stages {

        // ── STAGE 1 ──────────────────────────────────────
        stage('Checkout') {
            steps {
                echo '========================================'
                echo " Qualibytes GPT — Build #${BUILD_NUMBER}"
                echo " Time: ${new Date()}"
                echo '========================================'
                checkout scm
                sh 'ls -la'
            }
        }

        // ── STAGE 2 ──────────────────────────────────────
        stage('Build Docker Images') {
            steps {
                echo '=== Building Frontend & Backend Images ==='
                sh """
                    docker build -t ${DOCKER_CREDS_USR}/qualibytes-frontend:${BUILD_NUMBER} ./frontend
                    docker build -t ${DOCKER_CREDS_USR}/qualibytes-backend:${BUILD_NUMBER}  ./backend

                    docker tag ${DOCKER_CREDS_USR}/qualibytes-frontend:${BUILD_NUMBER} ${DOCKER_CREDS_USR}/qualibytes-frontend:latest
                    docker tag ${DOCKER_CREDS_USR}/qualibytes-backend:${BUILD_NUMBER}  ${DOCKER_CREDS_USR}/qualibytes-backend:latest

                    docker images | grep qualibytes
                """
            }
        }

        // ── STAGE 3 ──────────────────────────────────────
        stage('Push to Docker Hub') {
            steps {
                echo '=== Pushing images to Docker Hub ==='
                sh """
                    echo ${DOCKER_CREDS_PSW} | docker login -u ${DOCKER_CREDS_USR} --password-stdin

                    docker push ${DOCKER_CREDS_USR}/qualibytes-frontend:latest
                    docker push ${DOCKER_CREDS_USR}/qualibytes-frontend:${BUILD_NUMBER}

                    docker push ${DOCKER_CREDS_USR}/qualibytes-backend:latest
                    docker push ${DOCKER_CREDS_USR}/qualibytes-backend:${BUILD_NUMBER}

                    docker logout
                """
            }
        }

        // ── STAGE 4 ──────────────────────────────────────
        stage('Deploy to EC2') {
            steps {
                echo '=== Deploying to App Server ==='
                sshagent(['jenkins-agent']) {
                    sh """
                        scp -o StrictHostKeyChecking=no docker-compose.yml jenkins@${APP_SERVER_IP}:~/docker-compose.yml

                        ssh -o StrictHostKeyChecking=no jenkins@${APP_SERVER_IP} '
                            export DOCKER_USERNAME=${DOCKER_CREDS_USR}

                            echo ${DOCKER_CREDS_PSW} | docker login -u ${DOCKER_CREDS_USR} --password-stdin

                            docker compose pull frontend backend
                            docker compose up -d --no-deps frontend backend ollama

                            # Pull tinyllama only if not already downloaded
                            if ! docker exec qualibytes-ollama ollama list 2>/dev/null | grep -q tinyllama; then
                                echo "Pulling tinyllama model..."
                                docker exec qualibytes-ollama ollama pull tinyllama
                            fi

                            docker compose ps
                            docker logout
                        '
                    """
                }
            }
        }

        // ── STAGE 5 ──────────────────────────────────────
        stage('Health Check') {
            steps {
                echo '=== Verifying deployment ==='
                sshagent(['jenkins-agent']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no jenkins@${APP_SERVER_IP} '
                            sleep 5
                            curl --retry 5 --retry-delay 3 --fail \
                                 http://localhost:5000/health \
                                 && echo "Backend: HEALTHY" \
                                 || (echo "Backend: UNHEALTHY" && exit 1)
                        '
                    """
                }
            }
        }
    }

    post {
        success {
            echo '========================================'
            echo " Deployment SUCCESSFUL — Build #${BUILD_NUMBER}"
            echo " App URL: http://${APP_SERVER_IP}"
            echo '========================================'
        }
        failure {
            echo ' Pipeline FAILED — Check stage logs above'
        }
        always {
            cleanWs()
        }
    }
}
