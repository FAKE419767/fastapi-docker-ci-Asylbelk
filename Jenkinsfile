
pipeline {
    agent { label 'windows' }

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        IMAGE_NAME = 'fastapi-jenkins-demo'
        CONTAINER_NAME = 'fastapi-jenkins-demo'
        PYTHON_EXE = 'C:\\Users\\admin\\AppData\\Local\\Programs\\Python\\Python313\\python.exe'
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Cloning repository from GitHub...'
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Creating Python virtual environment...'

                bat '"%PYTHON_EXE%" -m venv .venv'

                echo 'Installing Python dependencies...'

                bat '.venv\\Scripts\\python.exe -m pip install --upgrade pip'
                bat '.venv\\Scripts\\python.exe -m pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                echo 'Running Pytest tests...'

                powershell '''
                    if (!(Test-Path reports)) {
                        New-Item -ItemType Directory -Path reports | Out-Null
                    }

                    if (Test-Path reports/pytest.xml) {
                        Remove-Item reports/pytest.xml
                    }
                '''

                bat '.venv\\Scripts\\python.exe -m pytest -v --junitxml=reports/pytest.xml'
            }

            post {
                always {
                    junit testResults: 'reports/pytest.xml',
                          allowEmptyResults: true
                }
            }
        }

        stage('Docker Build') {
            steps {
                echo 'Checking Docker...'

                bat 'docker info'

                echo 'Building Docker image...'

                bat 'docker build -t %IMAGE_NAME%:%BUILD_NUMBER% .'
            }
        }

        stage('Docker Deploy') {
            steps {
                echo 'Deploying FastAPI Docker container...'

                powershell '''
                    $ErrorActionPreference = 'Stop'

                    $existing = docker ps -aq --filter "name=^/$env:CONTAINER_NAME$"

                    if ($LASTEXITCODE -ne 0) {
                        throw 'Cannot query Docker containers'
                    }

                    if ($existing) {
                        Write-Host 'Removing previous container...'

                        docker rm -f $env:CONTAINER_NAME

                        if ($LASTEXITCODE -ne 0) {
                            throw 'Cannot remove previous container'
                        }
                    }

                    Write-Host 'Starting new container...'

                    docker run -d `
                        --name $env:CONTAINER_NAME `
                        --restart unless-stopped `
                        -p 127.0.0.1:8000:8000 `
                        "$($env:IMAGE_NAME):$($env:BUILD_NUMBER)"

                    if ($LASTEXITCODE -ne 0) {
                        throw 'Container startup failed'
                    }

                    Write-Host 'Docker container started!'
                '''
            }
        }

        stage('Health Check') {
            steps {
                echo 'Checking FastAPI health endpoint...'

                powershell '''
                    $ErrorActionPreference = 'Stop'

                    for ($attempt = 1; $attempt -le 30; $attempt++) {
                        try {
                            $response = Invoke-WebRequest `
                                -UseBasicParsing `
                                -Uri 'http://127.0.0.1:8000/health' `
                                -TimeoutSec 3

                            $data = $response.Content | ConvertFrom-Json

                            if ($response.StatusCode -eq 200 -and $data.status -eq 'ok') {
                                Write-Host 'SUCCESS: FastAPI is healthy!'
                                exit 0
                            }

                        } catch {
                            Write-Host "Waiting for application: attempt $attempt"
                            Write-Host $_.Exception.Message
                        }

                        Start-Sleep -Seconds 2
                    }

                    Write-Host 'FastAPI health check failed!'
                    docker logs --tail 100 $env:CONTAINER_NAME

                    throw 'Health Check FAILED'
                '''
            }
        }
    }

    post {
        success {
            echo '==================================='
            echo 'CI/CD PIPELINE SUCCESS!'
            echo '==================================='
            echo 'FastAPI is running successfully!'
            echo 'Swagger: http://localhost:8000/docs'
            echo 'Health: http://localhost:8000/health'
        }

        failure {
            echo '==================================='
            echo 'CI/CD PIPELINE FAILED!'
            echo '==================================='
            echo 'Check Jenkins Console Output.'
        }

        always {
            echo 'Pipeline execution completed.'
        }
    }
}
