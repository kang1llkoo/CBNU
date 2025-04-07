#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <string.h>

#define AI 17
#define SPADE "♠"
#define CLUB "♣"
#define DIA "◆"
#define HEART "♥"

// enum
enum shape { spade, club, dia, heart };
enum num { ace = 1, jack = 11, queen = 12, king = 13 };

// 카드 구조체
struct Card {
    int number; // 카드 숫자
    char shape; // 카드 모양
};

// 모든 카드
struct Card card_all[52];
int next;

// 선수
struct Player {
    int cash;  // 소지금
    int score; // 현재 점수
    int bust; // 버스트 여부
    struct Card card_player[21];
    int initial_cash; // 초기 소지금
};

struct Player player[2]; // 딜러와 플레이어 1만 사용

// 카드 섞는 함수
void shuffle()
{
    srand(time(NULL));
    for (int i = 0; i < 52; i++)
    {
        int index = rand() % 52;
        struct Card temp = card_all[index];
        card_all[index] = card_all[i];
        card_all[i] = temp;
    }
}

// 카드 채우는 함수
void filldeck()
{
    int i = 0;
    // 4개의 모양과 13개의 숫자를 짝지어서 카드 만듦
    for (int j = 0; j < 4; j++)
    {
        for (int k = 1; k < 14; k++)
        {
            card_all[i].number = k;
            card_all[i].shape = j;
            i++;
        }
    }
}

// 섞은 후 앞에서 부터 한장 나눠주는 함수
struct Card deal(int next)
{
    return card_all[next];
}

// 사용자가 뽑은 카드를 문자열이 아닌 카드 모양으로 출력
void printcard(int p, int turns)
{
    player[p].score = 0; // Initialize the player's score

    if (p == 0)
    {
        printf("\n<<DEALER>>\n");
    }
    else
    {
        printf("\n<<PLAYER%d>>\n", p);
    }

    for (int i = 0; i <= turns; i++)
    {
        printf("------- "); // 카드 라인의 시작 출력
    }

    printf("\n");

    for (int i = 0; i <= turns; i++)
    {
        printf("|%s    |", (player[p].card_player[i].shape == spade) ? SPADE : (player[p].card_player[i].shape == club) ? CLUB : (player[p].card_player[i].shape == dia) ? DIA : HEART);
    }

    printf("\n");

    for (int i = 0; i <= turns; i++)
    {
        // 카드의 숫자와 기호 함께 출력
        switch (player[p].card_player[i].number)
        {
        case ace:
            printf("|  A   |");
            if (p == 0) {
                // 딜러가 에이스를 가진 경우
                if (player[0].score <= 18) {
                    player[0].score += 11;
                }
                else {
                    player[0].score += 1;
                }
            }
            break;
        case jack:
            printf("|  J   |");
            player[p].score += 10;
            break;
        case queen:
            printf("|  Q   |");
            player[p].score += 10;
            break;
        case king:
            printf("|  K   |");
            player[p].score += 10;
            break;
        default:
            printf("|  %2d  |", player[p].card_player[i].number);
            player[p].score += player[p].card_player[i].number;
            break;
        }
    }

    printf("\n");

    for (int i = 0; i <= turns; i++)
    {
        // 카드의 기호 출력
        switch (player[p].card_player[i].shape)
        {
        case spade:
            printf("|    %s|", SPADE);
            break;
        case club:
            printf("|    %s|", CLUB);
            break;
        case dia:
            printf("|    %s|", DIA);
            break;
        case heart:
            printf("|    %s|", HEART);
            break;
        }
    }

    printf("\n");

    for (int i = 0; i <= turns; i++)
    {
        printf("------- "); // 카드 라인의 끝 출력
    }
    printf("\n");

    printf("score : %d\n", player[p].score);

    player[p].bust = player[p].score > 21;

    return;
}

int betting(struct Player player)
{
    int bet;

    printf("돈을 걸어봅시다! %d 중 얼마를 배팅하시겠습니까? ", player.cash);
    scanf("%d", &bet);

    if (bet > player.cash)
    {
        printf("이런이런... 돈이 부족하군요. 조금만 아껴야겠어요. 다시 입력 : ");
        scanf("%d", &bet);
        return bet;
    }
    else return bet;
}

// 게임을 시작
void stayorhit(int p, int turns)
{
    char answer;

    printf("\n##########TURN : PLAYER%d님##########\n\n", p);
    while (player[p].score <= 21)
    {
        printf("HIT을 원하시면 h를, STAY를 원하시면 s를 입력하세요[h/s]: ");
        scanf(" %c", &answer);

        if (answer == 'h' || answer == 'H')
        {
            turns++;
            player[p].card_player[turns] = deal(next++);
            printcard(p, turns);
            if (player[p].score > 21) {
                printf("21이 초과되었습니다. 패배\n");
                break;
            }
        }

        else if (answer == 's' || answer == 'S')
        {
            // stay를 입력한 이후에 ace 점수를 처리합니다.
            for (int i = 0; i <= turns; i++)
            {
                if (player[p].card_player[i].number == ace)
                {
                    printf("에이스 카드의 점수를 결정하세요 [1/11]: ");
                    int ace_value;
                    scanf("%d", &ace_value);
                    if (ace_value == 11)
                    {
                        player[p].score += 11; // 에이스는 이미 1로 처리되어 있으므로 11을 추가합니다.
                    }
                    else if (ace_value == 1) {
                        player[p].score += 1;
                    }
                    break; // 이미 처리된 에이스의 점수를 설정했으므로 반복문 종료
                }
            }
            break;
        }
        else
        {
            printf("HIT이면 h, STAY면 s라니까요.\n다시,");
        }
    }
}

// 딜러는 지능적으로 17까지만 안전하게 여기고 hit
void dealer(int turns)
{
    printf("\n##########DEALER's TURN##########\n\n");
    while (player[0].score < 21)
    {
        if (player[0].score < AI)
        {
            turns++;
            player[0].card_player[turns] = deal(next++);
            printcard(0, turns);
        }
        else
        {
            break;
        }
    }
    if (player[0].score > 21) player[0].score = 0;
}

// 게임 진행
void play()
{
    int turns = 1; // 두 장의 카드로 시작하기 때문에 초기 값을 1로 설정
    int push_flag = 0;
    int bet_total = 0;

    while (1)
    {
        int winner = -1; // -1: no winner, 0: dealer, 1: player
        int winnerscore = -1;
        int bet[2];

        if (push_flag == 0) bet_total = 0;

        // 플레이어 확인
        if (player[1].cash <= 0)
        {
            printf("!!! PLAYER1 파산하셨습니다. 100 다시 충전\n\n");
            player[1].cash += 100;
        }

        player[0].score = 0;
        player[1].score = 0;

        player[0].card_player[0] = deal(next++);
        player[0].card_player[1] = deal(next++);
        printcard(0, turns);

        printf("\n<<PLAYER1>>\n");
        printf("CASH : %d\n", player[1].cash);
        player[1].card_player[0] = deal(next++);
        player[1].card_player[1] = deal(next++);
        printcard(1, turns);

        printf("\nPLAYER1님, ");
        bet[1] = betting(player[1]);
        bet[0] = bet[1]; // 딜러의 배팅을 플레이어와 동일하게 설정
        bet_total = bet[0] + bet[1];

        stayorhit(1, turns);

        dealer(turns);

        printf("\n게임 결과>> DEALER: %d / PLAYER1: %d\n", player[0].score, player[1].score);

        // 게임 결과에 따른 처리
        if (player[0].score > 21 && player[1].score > 21) {
            printf("둘 다 21점을 초과했습니다. 딜러의 승리입니다.\n");
            winner = 0;
        }
        else if (player[0].score > 21) {
            printf("딜러가 21점을 초과했습니다. 플레이어의 승리입니다.\n");
            winner = 1;
        }
        else if (player[1].score > 21) {
            printf("플레이어가 21점을 초과했습니다. 딜러의 승리입니다.\n");
            winner = 0;
        }
        else if (player[0].score == player[1].score) {
            printf("비겼습니다.\n");
            push_flag = 1;
        }
        else if (player[0].score > player[1].score) {
            winner = 0;
        }
        else {
            winner = 1;
        }

        printf("prize: ");

        // 게임 결과에 따른 금액 처리
        if (push_flag) {
            // 비긴 경우 배팅금액을 잃지 않음
            printf("0\n");
        }
        else if (winner == 0) {
            player[1].cash -= bet[1];
            printf("%d\n", bet_total);
        }
        else if (winner == 1) {
            player[1].cash += bet[1];
            printf("%d\n", bet_total);
        }

        printf("\n결과>> P1 CASH : %d\n", player[1].cash);

        // 플레이어의 cash가 두 배가 되면 게임을 종료
        if (player[1].cash >= player[1].initial_cash * 2)
        {
            printf("축하합니다! 당신의 cash가 두 배가 되어 게임을 종료합니다.\n");
            break;
        }

        char answer;
        printf("계속하시겠습니까? ");
        scanf(" %c", &answer);

        if (answer == 'y' || answer == 'Y')
        {
            continue;
        }
        else
        {
            break;
        }
    }

    printf("게임이 종료됩니다... :)");
}

void reset()
{
    player[0].score = 0; player[1].score = 0;
    player[1].cash = 500;
    player[1].initial_cash = player[1].cash;

    filldeck(); shuffle(); next = 0;
}
void print_card_border(int length) {
    for (int i = 0; i < length; i++) {
        printf("┌─────┐ ");
    }
    printf("\n");
}
void print_card_numbers() {
    for (int i = 1; i <= 7; i++) {
        printf("│%2d   │ ", i);
    }
    printf("\n");

    for (int i = 1; i <= 7; i++) {
        printf("│  %s │ ", (i % 4 == 1) ? SPADE : (i % 4 == 2) ? CLUB : (i % 4 == 3) ? DIA : HEART);
    }
    printf("\n");

    for (int i = 1; i <= 7; i++) {
        printf("│   %2d│ ", i);
    }
    printf("\n");
}
void print_card_numbers_bot() {
    for (int i = 1; i <= 4; i++) {
        printf("│%2d   │ ", i + 6);
    }
    printf("│J    │ ");
    printf("│Q    │ ");
    printf("│K    │ ");
    printf("\n");

    for (int i = 1; i <= 4; i++) {
        printf("│  %s │ ", ((i + 6) % 4 == 1) ? SPADE : ((i + 6) % 4 == 2) ? CLUB : ((i + 6) % 4 == 3) ? DIA : HEART);
    }
    printf("│  %s │ ", DIA);
    printf("│  %s │ ", HEART);
    printf("│  %s │ ", SPADE);
    printf("\n");

    for (int i = 1; i <= 4; i++) {
        printf("│   %2d│ ", i + 6);
    }
    printf("│    J│ ");
    printf("│    Q│ ");
    printf("│    K│ ");
    printf("\n");
}
void print_card_bottom(int length) {
    for (int i = 0; i < length; i++) {
        printf("└─────┘ ");
    }
    printf("\n");
}

// 규칙을 출력하는 함수
void show_rules() {
    printf("\n블랙잭 규칙:\n");
    printf("┌───────────────────────────────────────────────────────────┐\n");
    printf("│  1. 목표는 카드의 합을 21에 가깝게 만드는 것입니다.       │\n");
    printf("│  2. 에이스(Ace)는 1점 또는 11점으로 계산할 수 있습니다.   │\n");
    printf("│  3. 잭(Jack), 퀸(Queen), 킹(King)은 각각 10점입니다.      │\n");
    printf("│  4. 다른 모든 카드는 숫자 그대로의 점수입니다.            │\n");
    printf("│  5. 카드는 플레이어와 딜러에게 나눠주며,                  │\n");
    printf("│     플레이어는 히트(h)하거나 스테이(s)할 수 있습니다.     │\n");
    printf("│  6. 딜러는 17점 이상일 때까지 카드를 받습니다.            │\n");
    printf("│  7. 21점을 초과하면 버스트(Bust)로 패배하게 됩니다.       │\n");
    printf("└───────────────────────────────────────────────────────────┘\n\n");
}

// 메뉴 출력하는 함수
void menu() {
    system("cls");
    // 카드 배열 출력 (윗부분)
    print_card_border(7);

    // 카드 숫자와 모양 출력
    print_card_numbers();

    // 카드 배열 출력 (아랫부분)
    print_card_bottom(7);

    // 메뉴 출력
    printf("     ┌───────────────────────────────────────────┐\n");
    printf("     │  블랙잭 게임에 오신 것을 환영합니다!      │\n");
    printf("     │                                           │\n");
    printf("     │  1. 시작                                  │\n");
    printf("     │  2. 규칙 보기                             │\n");
    printf("     │  3. 종료                                  │\n");
    printf("     └───────────────────────────────────────────┘\n");

    // 카드 배열 출력 (윗부분)
    print_card_border(7);

    // 카드 숫자와 모양 출력
    print_card_numbers_bot();

    // 카드 배열 출력 (아랫부분)
    print_card_bottom(7);
}

// 시작 함수
void start()
{
    int choice;
    do {
        menu();
        printf("메뉴를 선택하세요: ");
        scanf("%d", &choice);

        switch (choice) {
        case 1:
            reset();
            play();
            break;
        case 2:
            show_rules();
            printf("\n계속하려면 아무 키나 누르세요...");
            getchar(); // Enter key input from previous input
            getchar(); // Wait for user input
            break;
        case 3:
            printf("게임을 종료합니다. ㅂㅇㅂㅇ~\n");
            break;
        default:
            printf("잘못된 선택입니다. 다시 선택해주세요.\n");
            break;
        }
    } while (choice != 3);
}

int main(void)
{
    start();

    return 0;
}