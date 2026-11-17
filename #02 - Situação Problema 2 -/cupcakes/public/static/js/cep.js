// preenche rua, bairro, cidade e estado quando a pessoa digita o CEP (cartão 20)
// usa o serviço gratuito ViaCEP (https://viacep.com.br)
// se der erro ou não achar o CEP, a pessoa preenche na mão (o formulário funciona do mesmo jeito)

// pega os campos da página (se a página não tem o campo de cep, não faz nada)
var campoCep = document.getElementById("cep");
var campoRua = document.getElementById("rua");
var campoNumero = document.getElementById("numero");
var campoBairro = document.getElementById("bairro");
var campoCidade = document.getElementById("cidade");
var campoUf = document.getElementById("uf");
var avisoCep = document.getElementById("cep-aviso");

// guarda o último cep que já foi buscado (pra não buscar o mesmo cep duas vezes)
var ultimoCepBuscado = "";

// diz se tem uma busca rodando agora (pra não fazer duas buscas ao mesmo tempo)
var buscaEmAndamento = false;


// função que busca o endereço do cep e preenche os campos
function buscarCep() {
    // deixa só os números
    var cep = campoCep.value.replace(/\D/g, "");

    // só busca quando tem os 8 números
    if (cep.length != 8) {
        // a pessoa apagou o cep (ou ainda está digitando): esquece o último cep buscado
        // (antes eu não esquecia, e por isso digitar o mesmo cep de novo não preenchia nada)
        ultimoCepBuscado = "";
        return;
    }

    // não busca o mesmo cep duas vezes seguidas
    // MAS se a cidade está vazia (a pessoa apagou o endereço) busca de novo
    if (cep == ultimoCepBuscado) {
        if (campoCidade.value != "" || buscaEmAndamento == true) {
            return;
        }
    }
    ultimoCepBuscado = cep;
    buscaEmAndamento = true;

    avisoCep.textContent = "Buscando o endereço...";

    fetch("https://viacep.com.br/ws/" + cep + "/json/")
        .then(function (resposta) {
            return resposta.json();
        })
        .then(function (dados) {
            buscaEmAndamento = false;

            // o viacep devolve erro: true quando não acha o cep
            if (dados.erro) {
                avisoCep.textContent = "CEP não encontrado. Preencha o endereço à mão.";
                return;
            }

            // CEP geral de cidade pequena não tem rua nem bairro, então só preenche o que veio
            if (dados.logradouro) {
                campoRua.value = dados.logradouro;
            }
            if (dados.bairro) {
                campoBairro.value = dados.bairro;
            }
            campoCidade.value = dados.localidade;
            campoUf.value = dados.uf;

            avisoCep.textContent = "Endereço encontrado. Confira e digite o número.";
            campoNumero.focus();
        })
        .catch(function (erro) {
            // console.log(erro);
            buscaEmAndamento = false;
            avisoCep.textContent = "Não foi possível buscar o CEP agora. Preencha o endereço à mão.";
        });
}


// função que deixa o cep escrito do jeito certo (00000-000)
// aceita o que a pessoa digitar: 01001000, 01001-000, 01.001-000 ou 01001 000
function arrumarCep() {
    var cep = campoCep.value.replace(/\D/g, "");
    if (cep.length == 8) {
        campoCep.value = cep.substring(0, 5) + "-" + cep.substring(5);
    }
}


// só liga o javascript se a página tem todos os campos
if (campoCep != null && campoRua != null && campoNumero != null && campoBairro != null
        && campoCidade != null && campoUf != null && avisoCep != null) {

    campoCep.addEventListener("input", buscarCep);
    campoCep.addEventListener("blur", buscarCep);
    campoCep.addEventListener("blur", arrumarCep);
}