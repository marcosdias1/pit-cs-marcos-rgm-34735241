// tela de pagamento: escolhe entre PIX e cartão (cartão 11)


// pega os elementos da página
var escolhaForma = document.getElementById("escolha-forma");
var secaoPix = document.getElementById("secao-pix");
var secaoCartao = document.getElementById("secao-cartao");
var radios = document.querySelectorAll("input[name='forma_escolhida']");


// função que mostra só a forma de pagamento escolhida
function mostrarForma(forma) {
    if (forma == "cartao") {
        secaoPix.hidden = true;
        secaoCartao.hidden = false;
    } else {
        secaoPix.hidden = false;
        secaoCartao.hidden = true;
    }
}

// só liga o javascript se a página tem tudo
if (escolhaForma != null && secaoPix != null && secaoCartao != null) {

    // os botões de escolha começam escondidos no html, aqui eu mostro
    escolhaForma.hidden = false;

    // começa no PIX, a não ser que a página veio com erro do cartão (aí abre o cartão)
    var inicial = "pix";
    if (secaoCartao.getAttribute("data-abrir") == "1") {
        inicial = "cartao";
    }

    for (var i = 0; i < radios.length; i++) {
        if (radios[i].value == inicial) {
            radios[i].checked = true;
        }
        radios[i].addEventListener("change", function () {
            mostrarForma(this.value);
        });
    }

    mostrarForma(inicial);
}