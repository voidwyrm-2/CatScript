lt userInput = Casefold(GetText("please type something"))

if userInput == "exit" {
    print("exiting...")
    Exit(0)
} elseif userInput == "again" {
    goto 1
} elseif userInput == "fun" {
    print("the Spongebob or Plankton?")
    reply = Casefold(GetText())
    if reply == "Spongebob" {
        print("'F' is for friends who do stuff together,")
        print("'U' is for you and me,")
        print("'N' is for anywhere and any time at all, down here in the deep blue sea!")
    } elseif reply == "Spongebob" {
        print("'F' is for fire that burns down the whole town,")
        print("'U' is for Uranium. BOMBS!")
        print("'N' is for no survivors when you-")
    } else {
        print("invalid response")
        goto 10
    }
}