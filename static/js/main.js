document.addEventListener('DOMContentLoaded', function () {
            const select = document.getElementById('selectPercentual');
            const valorCabecalho = document.getElementById('valor-cabecalho');
            const btnSalvar = document.getElementById('btnSalvarPercentual');
            const input = document.getElementById('inputPercentual');
            const listaPercentuaisAdicionados = document.getElementById('listaPercentuaisAdicionados');

            // Percentuais fixos e percentuais de todos os usuários (passados pelo backend)
            const percentuaisFixos = {{ percentuais_fixos | tojson }};
            let percentuais = {{ percentuais_usuario | tojson }} || [];  // Se não tiver percentuais, usa um array vazio

            // Função para atualizar o select com percentuais fixos e percentuais de todos os usuários
            function atualizarSelectPercentuais() {
                select.innerHTML = ''; // Limpa o select antes de atualizar

                // Adiciona a opção "Omie" (sem percentual)
                const optionOmie = document.createElement('option');
                optionOmie.value = "omie";
                optionOmie.textContent = "Valor Omie";
                select.appendChild(optionOmie);

                // Adiciona a opção de "Mostrar todos"
                const optionTodos = document.createElement('option');
                optionTodos.value = "todos";
                optionTodos.textContent = "Mostrar todos";
                select.appendChild(optionTodos);

                // Adiciona as opções fixas (10%, 20%, 25%, 50%)
                percentuaisFixos.forEach((percentual) => {
                    const option = document.createElement('option');
                    option.value = percentual;
                    option.textContent = `+${percentual}%`;
                    select.appendChild(option);
                });

                // Adiciona os percentuais dos usuários (todos, logados e não logados)
                percentuais.forEach((percentual) => {
                    const option = document.createElement('option');
                    option.value = percentual;
                    option.textContent = `+${percentual}% (adicionado)`;
                    select.appendChild(option);
                });
            }

            // Função para atualizar a lista de percentuais visível na tela
            function atualizarListaPercentuais() {
                listaPercentuaisAdicionados.innerHTML = '';
                percentuais.forEach((percentual, index) => {
                    const item = document.createElement('li');
                    item.classList.add('list-group-item');
                    item.textContent = `+${percentual}%`;

                    const btnRemover = document.createElement('button');
                    btnRemover.classList.add('btn', 'btn-sm', 'btn-outline-danger', 'ms-3');
                    btnRemover.textContent = 'Excluir';
                    btnRemover.addEventListener('click', function () {
                        excluirPercentual(percentual, index);
                    });

                    item.appendChild(btnRemover);
                    listaPercentuaisAdicionados.appendChild(item);
                });
            }

            // Função para excluir o percentual
            function excluirPercentual(percentual, index) {
                fetch('/api/remover_percentual', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ percentual: percentual })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Remove o percentual da lista local
                        percentuais.splice(index, 1);
                        atualizarSelectPercentuais(); // Atualiza o select
                        atualizarListaPercentuais(); // Atualiza a lista visível
                    } else {
                        alert('Erro ao remover percentual.');
                    }
                })
                .catch(error => {
                    console.error('Erro ao excluir percentual:', error);
                });
            }

            // Inicializa as listas ao carregar a página
            atualizarSelectPercentuais();
            atualizarListaPercentuais();

            // Ao clicar no botão de salvar
            btnSalvar.addEventListener('click', function () {
                const valor = input.value.trim();

                if (valor === '' || isNaN(valor)) {
                    alert('Digite um percentual válido!');
                    return;
                }

                const valorNumerico = parseFloat(valor).toFixed(2);

                if (percentuais.includes(parseFloat(valorNumerico))) {
                    alert('Esse percentual já existe.');
                    return;
                }

                // Chama o backend via AJAX para adicionar o percentual
                fetch('/api/adicionar_percentual', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ percentual: valorNumerico })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.percentuais) {
                        percentuais.length = 0; // Limpa o array de percentuais
                        data.percentuais.forEach(p => percentuais.push(p)); // Atualiza com os novos percentuais
                        atualizarSelectPercentuais(); // Atualiza o select
                        atualizarListaPercentuais(); // Atualiza a lista visível
                    }
                })
                .catch(error => {
                    console.error('Erro ao adicionar percentual:', error);
                });

                input.value = '';
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalAdicionarPercentual'));
                modal.hide();
            });

            // Atualiza a exibição do valor com base no percentual selecionado
            select.addEventListener('change', function () {
                const percentualSelecionado = select.value;

                if (percentualSelecionado === "omie") {
                    // Quando "Omie" for selecionado, exibe o valor original
                    valorCabecalho.textContent = 'Valor Omie';
                } else if (percentualSelecionado && percentualSelecionado !== "todos") {
                    valorCabecalho.textContent = `Valor +${percentualSelecionado}%`;
                } else {
                    valorCabecalho.textContent = 'Valor Omie';
                }

                const linhas = document.querySelectorAll('tbody tr');
                linhas.forEach(function (linha) {
                    const valorUnitario = parseFloat(linha.querySelector('.valor-produto').getAttribute('data-valor'));
                    let valorComPercentual = valorUnitario;

                    if (percentualSelecionado && percentualSelecionado !== "omie" && percentualSelecionado !== "todos") {
                        valorComPercentual *= (1 + (parseFloat(percentualSelecionado) / 100));
                    }

                    linha.querySelector('.valor-produto').textContent = `R$ ${valorComPercentual.toFixed(2)}`;
                });
            });
        });