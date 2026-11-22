pipeline {
    agent any

    stages {

        stage('Get Code') {
            steps {
                git branch: 'develop', url: 'https://github.com/sergioglezz/demo-aws-serverless-cicd.git'
                echo WORKSPACE
                
                dir('config-temp') {
                    git branch: 'staging', url: 'https://github.com/sergioglezz/todo-list-aws-config.git'
                }
                
                sh '''
                    cp config-temp/samconfig.toml .
                    rm -rf config-temp
                '''
                
                sh 'ls -la'
                stash name: 'source-code', includes: '**/*'
            }
        }

        stage('Static Test') {
            steps {
                sh 'pip3 install flake8 bandit --break-system-packages -q'

                sh '/var/lib/jenkins/.local/bin/flake8 --exit-zero --format=pylint src > flake8.out'
                recordIssues tools: [flake8(name: 'Flake8', pattern: 'flake8.out')]

                sh '/var/lib/jenkins/.local/bin/bandit --exit-zero -r src -f custom -o bandit.out --msg-template "{abspath}:{line}: [{test_id}] {msg}"'
                recordIssues tools: [pyLint(name: 'Bandit', pattern: 'bandit.out')]
            }
        }
        
        stage('Deploy') {
            steps {
                sh 'sam build'
                
                sh '''
                    sam deploy \
                        --config-file samconfig.toml \
                        --config-env staging \
                        --no-confirm-changeset \
                        --no-fail-on-empty-changeset
                '''
                
                script {
                    env.API_URL = sh(
                        script: "aws cloudformation describe-stacks --stack-name todo-list-aws-staging --query 'Stacks[0].Outputs[?OutputKey==`BaseUrlApi`].OutputValue' --region us-east-1 --output text",
                        returnStdout: true
                    ).trim()
                    echo "API URL: ${env.API_URL}"
                }
            }
        }

        stage('Rest Test') {
            steps {
                sh 'pip3 install pytest requests --break-system-packages -q'
                sh """
                    export PATH=\$PATH:/var/lib/jenkins/.local/bin
                    export BASE_URL='${env.API_URL}'
                    pytest test/integration/todoApiTest.py --junitxml=result-rest.xml -v
                """
                junit 'result-rest.xml'
            }
        }

        stage('Promote') {
            steps {
                // gitUsernamePassword entrega el token a git mediante GIT_ASKPASS:
                // no se escribe en la URL del remoto, en .git/config ni en los logs
                withCredentials([gitUsernamePassword(
                    credentialsId: 'github-credentials',
                    gitToolName: 'Default'
                )]) {
                    sh '''
                        git config user.email "jenkins@devops.com"
                        git config user.name "Jenkins CI"

                        rm -f samconfig.toml
                        rm -f api_url.txt

                        git fetch origin

                        git checkout master
                        git pull origin master
                        
                        echo "Mergeando develop a master"
                        if git merge develop --no-edit; then
                            echo "Merge exitoso sin conflictos"
                        else
                            echo "Conflictos detectados"
                            git checkout --ours Jenkinsfile || true
                            git checkout --ours Jenkinsfile_agentes || true
                            git add Jenkinsfile Jenkinsfile_agentes
                            git commit -m "Merge develop to master (keeping master Jenkinsfiles)"
                        fi
                        
                        # Push
                        echo "Pusheando cambios"
                        git push origin master
                        
                        echo "✅ Promote completado exitosamente"
                            '''
                }
            }
        }

    }

    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline CI completado con exito!'
        }
        failure {
            echo 'Pipeline CI fallido!'
        }
    }
}