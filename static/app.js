// Inicializa o WebApp do Telegram
const tg = window.Telegram.WebApp;
tg.expand();

// Variáveis globais
let telegramId = null;
let selectedWhite = new Set();
let selectedRed = new Set();
const MAX_WHITE = 20;
const MAX_RED = 5;
let precoAposta = 5.0;
let saldoAtual = 0;

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    // Obter Telegram ID
    telegramId = tg.initDataUnsafe?.user?.id;
    
    if (!telegramId) {
        console.error('Telegram ID não encontrado');
        tg.showAlert('❌ Erro ao identificar usuário do Telegram');
        return;
    }

    // Aplicar máscaras
    aplicarMascaras();
    
    // Verificar cadastro
    verificarCadastro();
    
    // Buscar preço da aposta
    buscarPrecoAposta();
});

// ==================== NAVEGAÇÃO ====================

function showScreen(screenName) {
    // Esconder todas as telas
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    
    // Remover active de todas as tabs
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    
    // Mostrar tela selecionada
    const screen = document.getElementById(`screen-${screenName}`);
    if (screen) {
        screen.classList.add('active');
        
        // Ativar tab correspondente
        const tabs = document.querySelectorAll('.nav-tab');
        const screenOrder = ['jogar', 'historico', 'carteira', 'perfil'];
        const index = screenOrder.indexOf(screenName);
        if (index >= 0 && tabs[index]) {
            tabs[index].classList.add('active');
        }
        
        // Carregar dados específicos da tela
        if (screenName === 'historico') {
            carregarHistoricoApostas();
        } else if (screenName === 'carteira') {
            carregarHistoricoTransacoes();
            buscarSaldo();
        } else if (screenName === 'perfil') {
            carregarPerfil();
        } else if (screenName === 'jogar') {
            buscarSaldo();
            buscarPrecoAposta();
        }
    }
}

// ==================== CADASTRO ====================

function aplicarMascaras() {
    // Máscara para CPF
    const cpfInput = document.getElementById('cpf');
    if (cpfInput) {
        cpfInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 11) {
                value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{0,2})/, function(match, p1, p2, p3, p4) {
                    let result = p1;
                    if (p2) result += '.' + p2;
                    if (p3) result += '.' + p3;
                    if (p4) result += '-' + p4;
                    return result;
                });
                e.target.value = value;
            }
        });
    }

    // Máscara para telefone
    const telefoneInput = document.getElementById('telefone');
    if (telefoneInput) {
        telefoneInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 11) {
                if (value.length <= 10) {
                    value = value.replace(/(\d{2})(\d{4})(\d{0,4})/, function(match, p1, p2, p3) {
                        let result = '';
                        if (p1) result = '(' + p1 + ')';
                        if (p2) result += ' ' + p2;
                        if (p3) result += '-' + p3;
                        return result;
                    });
                } else {
                    value = value.replace(/(\d{2})(\d{5})(\d{0,4})/, function(match, p1, p2, p3) {
                        let result = '';
                        if (p1) result = '(' + p1 + ')';
                        if (p2) result += ' ' + p2;
                        if (p3) result += '-' + p3;
                        return result;
                    });
                }
                e.target.value = value;
            }
        });
    }
}

async function verificarCadastro() {
    try {
        const response = await fetch('/api/player/check-registration', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ telegram_id: telegramId })
        });

        const data = await response.json();
        
        if (data.cadastro_completo) {
            // Usuário cadastrado - mostrar tela de jogar
            document.getElementById('screen-cadastro').style.display = 'none';
            document.getElementById('nav-tabs').style.display = 'flex';
            showScreen('jogar');
            buscarSaldo();
            createGrid('grid-white', 69, 'white');
            createGrid('grid-red', 26, 'red');
        } else {
            // Usuário não cadastrado - mostrar cadastro
            document.getElementById('screen-cadastro').classList.add('active');
            document.getElementById('nav-tabs').style.display = 'none';
        }
    } catch (error) {
        console.error('Erro ao verificar cadastro:', error);
        document.getElementById('screen-cadastro').classList.add('active');
        document.getElementById('nav-tabs').style.display = 'none';
    }
}

function validarCPF(cpf) {
    cpf = cpf.replace(/\D/g, '');
    if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false;
    
    let soma = 0;
    for (let i = 0; i < 9; i++) soma += parseInt(cpf.charAt(i)) * (10 - i);
    let resto = 11 - (soma % 11);
    let digito1 = resto >= 10 ? 0 : resto;
    
    soma = 0;
    for (let i = 0; i < 10; i++) soma += parseInt(cpf.charAt(i)) * (11 - i);
    resto = 11 - (soma % 11);
    let digito2 = resto >= 10 ? 0 : resto;
    
    return digito1 === parseInt(cpf.charAt(9)) && digito2 === parseInt(cpf.charAt(10));
}

async function enviarCadastro(event) {
    event.preventDefault();
    
    const nome = document.getElementById('nome').value.trim();
    const cpf = document.getElementById('cpf').value.trim();
    const pix = document.getElementById('pix').value.trim();
    const telefone = document.getElementById('telefone').value.trim();
    const cidade = document.getElementById('cidade').value.trim();
    const estado = document.getElementById('estado').value;

    if (!nome || !cpf || !pix || !telefone) {
        tg.showAlert('Por favor, preencha todos os campos obrigatórios.');
        tg.HapticFeedback.notificationOccurred('error');
        return;
    }

    if (!validarCPF(cpf)) {
        tg.showAlert('❌ CPF inválido! Verifique e tente novamente.');
        tg.HapticFeedback.notificationOccurred('error');
        return;
    }

    try {
        const dados = {
            action: 'cadastro_usuario',
            nome: nome,
            cpf: cpf,
            pix: pix,
            telefone: telefone,
            cidade: cidade || null,
            estado: estado || null
        };

        tg.sendData(JSON.stringify(dados));
        
        tg.showAlert('✅ Cadastro realizado com sucesso!');
        tg.HapticFeedback.notificationOccurred('success');
        
        setTimeout(() => {
            verificarCadastro();
        }, 1000);
        
    } catch (error) {
        console.error('Erro ao enviar cadastro:', error);
        tg.showAlert('❌ Erro ao realizar cadastro. Tente novamente.');
        tg.HapticFeedback.notificationOccurred('error');
    }
}

// ==================== SALDO ====================

async function buscarSaldo() {
    try {
        const response = await fetch(`/finance/balance/${telegramId}`);
        const data = await response.json();
        
        if (data.saldo !== undefined) {
            saldoAtual = data.saldo;
            const saldoFormatado = formatarMoeda(data.saldo);
            document.getElementById('saldo-header').textContent = saldoFormatado;
            
            const saldoCarteira = document.getElementById('saldo-carteira');
            if (saldoCarteira) saldoCarteira.textContent = saldoFormatado;
        }
    } catch (error) {
        console.error('Erro ao buscar saldo:', error);
    }
}

function formatarMoeda(valor) {
    return valor.toFixed(2).replace('.', ',');
}

// ==================== PREÇO DA APOSTA ====================

async function buscarPrecoAposta() {
    try {
        const response = await fetch('/api/player/config/bet-price');
        const data = await response.json();
        
        if (data.preco) {
            precoAposta = data.preco;
            document.getElementById('preco-aposta').textContent = formatarMoeda(data.preco);
            
            if (data.premio_total) {
                document.getElementById('premio-total').textContent = formatarMoeda(data.premio_total);
            }
        }
    } catch (error) {
        console.error('Erro ao buscar preço da aposta:', error);
    }
}

// ==================== GRID DE NÚMEROS ====================

function createGrid(containerId, maxNum, type) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    for (let i = 1; i <= maxNum; i++) {
        const ball = document.createElement('div');
        ball.className = 'ball';
        ball.innerText = i;
        ball.onclick = () => toggleSelection(i, type, ball);
        container.appendChild(ball);
    }
}

function toggleSelection(num, type, element) {
    if (type === 'white') {
        if (selectedWhite.has(num)) {
            selectedWhite.delete(num);
            element.classList.remove('selected-white');
        } else {
            if (selectedWhite.size >= MAX_WHITE) {
                tg.HapticFeedback.notificationOccurred('error');
                return;
            }
            selectedWhite.add(num);
            element.classList.add('selected-white');
            tg.HapticFeedback.selectionChanged();
        }
    } else {
        if (selectedRed.has(num)) {
            selectedRed.delete(num);
            element.classList.remove('selected-red');
        } else {
            if (selectedRed.size >= MAX_RED) {
                tg.HapticFeedback.notificationOccurred('error');
                return;
            }
            selectedRed.add(num);
            element.classList.add('selected-red');
            tg.HapticFeedback.selectionChanged();
        }
    }
    updateUI();
}

function updateUI() {
    document.getElementById('count-white').innerText = `⚪ ${selectedWhite.size}/${MAX_WHITE}`;
    document.getElementById('count-red').innerText = `🔴 ${selectedRed.size}/${MAX_RED}`;

    const btn = document.getElementById('btn-confirmar');
    if (selectedWhite.size === MAX_WHITE && selectedRed.size === MAX_RED) {
        btn.disabled = false;
    } else {
        btn.disabled = true;
    }
}

function gerarSurpresinha() {
    // Limpar seleção
    document.querySelectorAll('.ball').forEach(b => {
        b.classList.remove('selected-white', 'selected-red');
    });
    selectedWhite.clear();
    selectedRed.clear();

    // Gerar números brancos
    while(selectedWhite.size < MAX_WHITE) {
        let r = Math.floor(Math.random() * 69) + 1;
        selectedWhite.add(r);
    }

    // Gerar powerballs
    while(selectedRed.size < MAX_RED) {
        let r = Math.floor(Math.random() * 26) + 1;
        selectedRed.add(r);
    }

    // Atualizar visual
    const whiteBalls = document.getElementById('grid-white').children;
    selectedWhite.forEach(num => whiteBalls[num-1].classList.add('selected-white'));

    const redBalls = document.getElementById('grid-red').children;
    selectedRed.forEach(num => redBalls[num-1].classList.add('selected-red'));

    updateUI();
    tg.HapticFeedback.notificationOccurred('success');
}

function confirmarAposta() {
    // Verificar saldo
    if (saldoAtual < precoAposta) {
        tg.showAlert(`❌ Saldo insuficiente! Você precisa de R$ ${formatarMoeda(precoAposta)}`);
        tg.HapticFeedback.notificationOccurred('error');
        showScreen('carteira');
        return;
    }

    const dados = {
        white: Array.from(selectedWhite),
        red: Array.from(selectedRed),
        action: 'aposta_realizada'
    };
    
    tg.sendData(JSON.stringify(dados));
    tg.showAlert('✅ Aposta enviada com sucesso!');
    tg.HapticFeedback.notificationOccurred('success');
}

// ==================== HISTÓRICO DE APOSTAS ====================

async function carregarHistoricoApostas() {
    const container = document.getElementById('lista-apostas');
    container.innerHTML = '<div class="loading"><div class="spinner"></div><div>Carregando...</div></div>';
    
    try {
        const response = await fetch(`/api/player/history/bets/${telegramId}`);
        const data = await response.json();
        
        if (data.apostas && data.apostas.length > 0) {
            container.innerHTML = '';
            data.apostas.forEach(aposta => {
                const item = criarItemAposta(aposta);
                container.appendChild(item);
            });
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🎮</div>
                    <div>Nenhuma aposta realizada ainda</div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Erro ao carregar histórico:', error);
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">❌</div>
                <div>Erro ao carregar histórico</div>
            </div>
        `;
    }
}

function criarItemAposta(aposta) {
    const div = document.createElement('div');
    div.className = 'history-item';
    
    const statusClass = `status-${aposta.status_color}`;
    
    div.innerHTML = `
        <div class="history-header">
            <div>
                <div style="font-weight: bold;">${aposta.concurso_nome}</div>
                <div class="history-date">${aposta.data_aposta}</div>
            </div>
            <span class="status-badge ${statusClass}">${aposta.status}</span>
        </div>
        <div class="numbers-display">
            ${aposta.numeros_brancos.map(n => `<div class="number-badge number-white">${n}</div>`).join('')}
            ${aposta.numeros_vermelhos.map(n => `<div class="number-badge number-red">${n}</div>`).join('')}
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 0.9rem;">
            <div>Acertos: <strong>${aposta.acertos}</strong></div>
            <div>Valor: <strong>R$ ${formatarMoeda(aposta.valor_pago)}</strong></div>
            ${aposta.valor_premio > 0 ? `<div style="color: var(--accent-color);">Prêmio: <strong>R$ ${formatarMoeda(aposta.valor_premio)}</strong></div>` : ''}
        </div>
    `;
    
    return div;
}

// ==================== CARTEIRA ====================

function mostrarDeposito() {
    document.getElementById('deposito-form').style.display = 'block';
    document.getElementById('form-valor-deposito').style.display = 'block';
    document.getElementById('qrcode-pix-container').style.display = 'none';
}

function voltarCarteira() {
    document.getElementById('deposito-form').style.display = 'none';
    carregarHistoricoTransacoes();
}

function voltarValorDeposito() {
    document.getElementById('form-valor-deposito').style.display = 'block';
    document.getElementById('qrcode-pix-container').style.display = 'none';
}

function setValorDeposito(valor) {
    document.getElementById('valor-deposito').value = valor;
    tg.HapticFeedback.selectionChanged();
}

async function gerarPixDeposito() {
    const valor = parseFloat(document.getElementById('valor-deposito').value);
    
    if (!valor || valor < 5) {
        tg.showAlert('❌ Valor mínimo para depósito é R$ 5,00');
        tg.HapticFeedback.notificationOccurred('error');
        return;
    }

    try {
        tg.MainButton.setText('Gerando PIX...');
        tg.MainButton.show();
        tg.MainButton.showProgress();

        const response = await fetch('/finance/deposit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                telegram_id: telegramId,
                valor: valor
            })
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('qrcode-image').src = `data:image/png;base64,${data.qr_code_base64}`;
            document.getElementById('pix-code').value = data.pix_code;
            
            document.getElementById('form-valor-deposito').style.display = 'none';
            document.getElementById('qrcode-pix-container').style.display = 'block';
            
            tg.HapticFeedback.notificationOccurred('success');
            tg.MainButton.hide();
        } else {
            throw new Error(data.detail || 'Erro ao gerar PIX');
        }
    } catch (error) {
        console.error('Erro ao gerar PIX:', error);
        tg.showAlert(`❌ ${error.message}`);
        tg.HapticFeedback.notificationOccurred('error');
        tg.MainButton.hide();
    }
}

function copiarPixCode() {
    const pixCode = document.getElementById('pix-code');
    pixCode.select();
    pixCode.setSelectionRange(0, 99999);
    
    try {
        document.execCommand('copy');
        tg.showAlert('✅ Código PIX copiado!');
        tg.HapticFeedback.notificationOccurred('success');
    } catch (error) {
        navigator.clipboard.writeText(pixCode.value).then(() => {
            tg.showAlert('✅ Código PIX copiado!');
            tg.HapticFeedback.notificationOccurred('success');
        }).catch(() => {
            tg.showAlert('❌ Erro ao copiar. Copie manualmente.');
        });
    }
}

function mostrarSaque() {
    tg.showAlert('🚧 Funcionalidade de saque em desenvolvimento');
}

async function carregarHistoricoTransacoes() {
    const container = document.getElementById('lista-transacoes');
    container.innerHTML = '<div class="loading"><div class="spinner"></div><div>Carregando...</div></div>';
    
    try {
        const response = await fetch(`/api/player/history/transactions/${telegramId}`);
        const data = await response.json();
        
        if (data.transacoes && data.transacoes.length > 0) {
            container.innerHTML = '';
            data.transacoes.forEach(transacao => {
                const item = criarItemTransacao(transacao);
                container.appendChild(item);
            });
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">💰</div>
                    <div>Nenhuma transação realizada ainda</div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Erro ao carregar transações:', error);
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">❌</div>
                <div>Erro ao carregar transações</div>
            </div>
        `;
    }
}

function criarItemTransacao(transacao) {
    const div = document.createElement('div');
    div.className = 'transaction-item';
    
    const valorClass = transacao.valor >= 0 ? 'var(--accent-color)' : 'var(--red-color)';
    const valorSinal = transacao.valor >= 0 ? '+' : '';
    
    div.innerHTML = `
        <div class="transaction-icon">${transacao.icone}</div>
        <div class="transaction-details">
            <div class="transaction-title">${transacao.descricao}</div>
            <div class="transaction-date">${transacao.data}</div>
        </div>
        <div class="transaction-value" style="color: ${valorClass};">
            ${valorSinal}R$ ${formatarMoeda(Math.abs(transacao.valor))}
        </div>
    `;
    
    return div;
}

// ==================== PERFIL ====================

async function carregarPerfil() {
    try {
        // Buscar estatísticas
        const statsResponse = await fetch(`/api/player/stats/${telegramId}`);
        const stats = await statsResponse.json();
        
        // Atualizar nome e telefone
        document.getElementById('perfil-nome').textContent = stats.nome || 'Usuário';
        
        // Buscar dados do usuário
        const userResponse = await fetch('/api/player/check-registration', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ telegram_id: telegramId })
        });
        const userData = await userResponse.json();
        
        if (userData.usuario) {
            document.getElementById('perfil-telefone').textContent = userData.usuario.telefone || '-';
            document.getElementById('perfil-cpf').textContent = userData.usuario.cpf || '-';
            document.getElementById('perfil-pix').textContent = userData.usuario.pix || '-';
            document.getElementById('perfil-cidade').textContent = userData.usuario.cidade || '-';
            document.getElementById('perfil-estado').textContent = userData.usuario.estado || '-';
        }
        
        // Atualizar estatísticas
        document.getElementById('stat-apostas').textContent = stats.total_apostas || 0;
        document.getElementById('stat-vitorias').textContent = stats.total_vitorias || 0;
        document.getElementById('stat-gasto').textContent = 'R$ ' + formatarMoeda(stats.total_gasto || 0);
        document.getElementById('stat-ganho').textContent = 'R$ ' + formatarMoeda(stats.total_ganho || 0);
        
    } catch (error) {
        console.error('Erro ao carregar perfil:', error);
    }
}

