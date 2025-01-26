Este relatório descreve o desenvolvimento de uma runtime personalizada para funções lambda, criada para substituir a imagem de execução fornecida pelos instrutores; Conforme solicitado na tarefa 3 do trabalho. O objetivo principal é construir um runtime serverless que seja compatível com as funções implementadas nas tasks 1 e 2, garantindo que os parâmetros sejam passados corretamente e que os valores retornados sejam encaminhados para os destinos adequados. 

O runtime original utiliza o Redis para ler periodicamente dados e passá-los como parâmetros para a função - por meio das variáveis input e context - além de armazenar os resultados no Redis para serem posteriormente acessados. Para isso, o usuário deve passar uma série de variáveis de ambiente, definidas em diversos ConfigMaps.

Sendo assim, o runtime implementado deve manter o suporte e compatibilidade com o runtime fornecido pelos instrutores.

## Detalhes de Implementação

Assim como no runtime original, toda a configuração da runtime é feita via ConfigMaps, com algumas variáveis especiais:

**REDIS_HOST**: o endereço IP do serviço Redis em execução
**REDIS_PORT**: a porta do serviço Redis em execução
**REDIS_INPUT_KEY**: a chave que a função lambda consome
**REDIS_OUPUT_KEY**: a chave onde a função lambda escreve seu resultado json 

**POOL_INTERNAL**: o intervalo (segundos) onde a função lambda é executada -> 5 segundos por padrão
**ZIP_FILE**: a URL da pasta zip com o código a ser executadao 
**FUNCTION_HANDLER**: nome da função a ser chamada -> handler por padrão


As primeiras 4 variáveis também existem no runtime original, mantendo a compatibilidade com a outra implementação. Além disso, é possível que o usuário monte a função serveless por meio do ConfigMap "pyfile", da mesma forma que o runtime disponibilizado. 

Entretanto, a runtime implementada possui algumas extensões, como, por exemplo, suporte a módulos python complexo por meio dos arquivos zip. Sempre que essa variável existe, todo o código python da pasta é carregada em memória e a função a ser executada é aquela com o nome definido em FUNCTION_HANDLER. No caso em que existe tanto uma configuração via "pyfile" quanto um arquivo zip, apenas o código existente em "pyfile" é executado. 


Dessa forma, o novo runtime implementado é completamente compatível com o runtime original, já que ambos implementam os mesmos contratos com comportamentos parecidos.
