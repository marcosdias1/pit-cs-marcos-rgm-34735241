// tela de detalhes: botões de mais e menos da quantidade (cartão 05)

// pega os elementos da página
var campoQuantidade = document.getElementById("quantidade");
var botaoMais = document.getElementById("mais");
var botaoMenos = document.getElementById("menos");

// os botões começam escondidos no html (se o javascript não carregar, o campo de número já funciona sozinho)
botaoMais.hidden = false;
botaoMenos.hidden = false;


// função que soma ou diminui a quantidade (nunca menos que 1 nem mais que 99)
function mudarQuantidade(mudanca) {
    var atual = parseInt(campoQuantidade.value);

    // se apagou ou digitou besteira, volta pra 1
    if (isNaN(atual)) {
        atual = 1;
    }

    var nova = atual + mudanca;
    if (nova < 1) {
        nova = 1;
    }
    if (nova > 99) {
        nova = 99;
    }
    campoQuantidade.value = nova;
}

botaoMais.addEventListener("click", function () {
    mudarQuantidade(1);
});

botaoMenos.addEventListener("click", function () {
    mudarQuantidade(-1);
});