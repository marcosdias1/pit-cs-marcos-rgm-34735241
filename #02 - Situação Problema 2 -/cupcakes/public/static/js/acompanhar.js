// tela de acompanhamento do pedido (cartão 12)
// de tempos em tempos pergunta pro servidor qual é o status do pedido e atualiza a tela, sem recarregar a página (o cartão sugeria WebSockets, aqui eu uso um jeito mais simples que dá o mesmo resultado pra quem usa)


// pega os elementos da página
var caixa = document.getElementById("acompanhamento");
var statusTexto = document.getElementById("status-texto");
var statusDescricao = document.getElementById("status-descricao");
var previsao = document.getElementById("previsao");
var linhaDoTempo = document.getElementById("linha-do-tempo");
var avisoJs = document.getElementById("aviso-js");

// de quanto em quanto tempo pergunta pro servidor (em milissegundos)
var TEMPO_ENTRE_CONSULTAS = 5000;

// guarda o "relógio" da consulta (pra poder parar quando o pedido for entregue)
var relogio = null;


// função que desenha de novo a lista de etapas
function desenharEtapas(etapas) {
    linhaDoTempo.innerHTML = "";

    for (var i = 0; i < etapas.length; i++) {
        var item = document.createElement("li");
        item.className = "etapa etapa-" + etapas[i].estado;
        // textContent é mais seguro que innerHTML
        item.textContent = etapas[i].texto;
        if (etapas[i].estado == "atual") {
            item.setAttribute("aria-current", "step");
        }
        linhaDoTempo.appendChild(item);
    }
}


// função que mostra uma mensagem de aviso em cima do status
function mostrarAviso(texto) {
    avisoJs.textContent = texto;
    avisoJs.hidden = false;
}


// função que pergunta pro servidor e atualiza a tela
function atualizar() {
    var numero = caixa.getAttribute("data-numero");

    fetch("/api/pedido/" + numero + "/status")
        .then(function (resposta) {
            // 401 quer dizer que a sessão acabou, então volta pro login
            if (resposta.status == 401) {
                window.location.href = "/login";
                return { sessaoAcabou: true };
            }
            return resposta.json();
        })
        .then(function (dados) {
            if (dados.sessaoAcabou) {
                return;
            }
            // o servidor avisou que deu erro (a gente tenta de novo na próxima vez)
            if (dados.erro) {
                mostrarAviso(dados.erro);
                return;
            }

            avisoJs.hidden = true;
            statusTexto.textContent = dados.status_texto;
            statusDescricao.textContent = dados.descricao;
            previsao.textContent = dados.previsao;
            desenharEtapas(dados.etapas);

            // se já foi entregue, não precisa mais perguntar
            if (dados.entregue) {
                clearInterval(relogio);
            }
        })
        .catch(function (erro) {
            // console.log(erro);
            mostrarAviso("Sem conexão com o servidor. Vamos tentar de novo em instantes.");
        });
}


// só liga o javascript se a página tem tudo, e se o pedido ainda não foi entregue
if (caixa != null && statusTexto != null && statusDescricao != null && previsao != null
        && linhaDoTempo != null && avisoJs != null) {

    if (caixa.getAttribute("data-entregue") == "0") {
        relogio = setInterval(atualizar, TEMPO_ENTRE_CONSULTAS);
    }
}