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
    }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Install Dependencies') {
            steps {
               bat '"C:\\Users\\admin\\AppData\\Local\\Programs\\Python\\Python313\\python.exe" -m venv .venv'
                bat '.venv\\Scripts\\python.exe -m pip install -r requirements.txt'
            }
        }
        stage('Run Tests') {
            steps {
                powershell 'if (Test-Path reports/pytest.xml) { Remove-Item -LiteralPath reports/pytest.xml }'
                bat '.venv\\Scripts\\python.exe -m pytest -v --junitxml=reports/pytest.xml'
            }
            post {
                always { junit testResults: 'reports/pytest.xml', allowEmptyResults: true }
            }
        }
        stage('Docker Build') {
            steps {
                bat 'docker info'
                bat 'docker build -t %IMAGE_NAME%:%BUILD_NUMBER% .'
            }
        }
        stage('Docker Deploy') {
            steps {
                powershell '''
                    $ErrorActionPreference = 'Stop'
                    $existing = docker ps -aq --filter "name=^/$env:CONTAINER_NAME$"
                    if ($LASTEXITCODE -ne 0) { throw 'Cannot query Docker containers' }
                    if ($existing) {
                        docker rm -f $env:CONTAINER_NAME
                        if ($LASTEXITCODE -ne 0) { throw 'Cannot remove previous container' }
                    }
                    docker run -d --name $env:CONTAINER_NAME --restart unless-stopped -p 127.0.0.1:8000:8000 "$($env:IMAGE_NAME):$($env:BUILD_NUMBER)"
                    if ($LASTEXITCODE -ne 0) { throw 'Container startup failed' }
                '''
            }
        }
        stage('Health Check') {
            steps {
                powershell '''
                    $ErrorActionPreference = 'Stop'
                    for ($attempt = 1; $attempt -le 30; $attempt++) {
                        try {
                            $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8000/health' -TimeoutSec 2
                            $health = docker inspect --format '{{.State.Health.Status}}' $env:CONTAINER_NAME
                            if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect container' }
                            if ($response.StatusCode -eq 200 -and ($response.Content | ConvertFrom-Json).status -eq 'ok' -and $health -eq 'healthy') {
                                Write-Host 'Application is healthy'
                                exit 0
                            }
                        } catch { Write-Host "Waiting for application: attempt $attempt" }
                        Start-Sleep -Seconds 2
                    }
                    docker logs --tail 100 $env:CONTAINER_NAME
                    throw 'Application did not become healthy before the deadline'
                '''
            }
        }
    }
    post {
        success { echo 'Result: SUCCESS. API: http://localhost:8000/docs' }
        failure { echo 'Result: FAILURE. Inspect Console Output and test results.' }
    }
}
